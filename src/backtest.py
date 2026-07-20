"""RCT holdout 政策回測：agent vs 天真基準。

RCT 保證 treated / control 可比，所以任一目標群的增量轉換率可直接用
mean(y | t=1) − mean(y | t=0) 估計——這是選 RCT 資料集的全部理由。

核心對照組是 propensity_top（發給「最可能買的人」）：
分數高 ≠ 增量高，sure_thing 不需要券也會買，發券純虧。
"""

import pandas as pd
from sklift.metrics import qini_auc_score

import params as P


def qini(y_true, tau_hat, treated):
    """Qini AUC：uplift 排序品質的標準指標（越高越能把 persuadables 排前面）。"""
    return float(qini_auc_score(y_true, tau_hat, treated))


def incremental_profit(df, target_mask, n_abstain=0):
    """目標群的估計增量利潤。回傳 (profit, n_target, inc_rate)。"""
    sub = df[target_mask]
    n_target = len(sub)
    if n_target == 0:
        inc = 0.0
    else:
        t1 = sub.loc[sub["treated"] == 1, "converted"]
        t0 = sub.loc[sub["treated"] == 0, "converted"]
        inc = (t1.mean() if len(t1) else 0.0) - (t0.mean() if len(t0) else 0.0)
    profit = (
        n_target * (inc * P.AOV * P.GROSS_MARGIN - P.EXPECTED_COUPON_COST)
        - n_abstain * P.REVIEW_COST
    )
    return float(profit), int(n_target), float(inc)


def compare_policies(holdout, decisions, tau_hat, propensity):
    """五種政策同場比較，目標數對齊 agent 的 ISSUE 數以求公平。"""
    df = holdout.copy()
    df["_tau"] = tau_hat
    df["_prop"] = propensity
    n_issue = int((decisions == "ISSUE").sum())
    n_abstain = int((decisions == "ABSTAIN").sum())

    prop_top = df["_prop"].rank(ascending=False, method="first") <= n_issue
    tau_top = df["_tau"].rank(ascending=False, method="first") <= n_issue

    rows = []
    for name, mask, abstain in [
        ("agent（會拒絕）", (decisions == "ISSUE").to_numpy(), n_abstain),
        ("uplift_top（同模型、不拒絕）", tau_top.to_numpy(), 0),
        ("propensity_top（發給最可能買的人）", prop_top.to_numpy(), 0),
        ("send_all（全發）", pd.Series(True, index=df.index).to_numpy(), 0),
        ("send_none（全不發）", pd.Series(False, index=df.index).to_numpy(), 0),
    ]:
        profit, n_target, inc = incremental_profit(df, mask, abstain)
        rows.append(
            {
                "policy": name,
                "n_target": n_target,
                "inc_rate": round(inc, 4),
                "est_profit": round(profit, 2),
            }
        )
    return pd.DataFrame(rows)
