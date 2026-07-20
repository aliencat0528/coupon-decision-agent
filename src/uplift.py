"""Uplift 層：scikit-uplift TwoModels（T-learner）＋ bootstrap 信賴區間。

規則（CA-003）：所有數值估計出自本層統計模型；LLM 不做數值預測。
propensity 模型只作為 backtest 的天真基準（「發給最可能買的人」）。
"""

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklift.models import TwoModels

import params as P


def _base_learner(seed):
    return GradientBoostingClassifier(n_estimators=60, max_depth=3, random_state=seed)


def fit_uplift_with_ci(x_train, y_train, t_train, x_eval, rounds=P.BOOTSTRAP_ROUNDS,
                       seed=P.RANDOM_SEED):
    """bootstrap 重抽訓練集 → 每輪重訓 T-learner → 對 x_eval 的 uplift 分佈。

    回傳 (tau_hat, tau_lo, tau_hi)：逐客戶點估計與百分位信賴區間。
    信賴區間反映的是「模型對這位客戶增量的把握」，是拒絕決策的直接輸入。
    """
    rng = np.random.default_rng(seed)
    n = len(x_train)
    preds = np.empty((rounds, len(x_eval)))
    for b in range(rounds):
        idx = rng.integers(0, n, n)
        # 重抽後需兩組皆存在，否則 T-learner 無法訓練
        if t_train.iloc[idx].nunique() < 2:
            idx = np.arange(n)
        model = TwoModels(_base_learner(seed + b), _base_learner(seed + b), method="vanilla")
        model.fit(x_train.iloc[idx], y_train.iloc[idx], t_train.iloc[idx])
        preds[b] = model.predict(x_eval)
    return (
        preds.mean(axis=0),
        np.percentile(preds, P.CI_LO_PCT, axis=0),
        np.percentile(preds, P.CI_HI_PCT, axis=0),
    )


def fit_propensity(x_train, y_train, x_eval, seed=P.RANDOM_SEED):
    """天真基準：P(轉換)，忽略 treatment。demo「propensity ≠ uplift」用。"""
    model = _base_learner(seed).fit(x_train, y_train)
    return model.predict_proba(x_eval)[:, 1]
