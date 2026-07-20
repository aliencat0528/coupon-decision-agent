"""資料層：載入 Hillstrom（真 RCT）或生成 synthetic RCT。

synthetic DGP 內建四種「隱藏」客群（sure_thing / persuadable / lost_cause / sleeping_dog），
用來驗證核心轉折點「propensity ≠ uplift」：最可能買的人（sure_thing）幾乎沒有增量，
該發券的是 persuadables。隱藏類型只放在 `_true_type` 診斷欄，不進模型特徵。
"""

import numpy as np
import pandas as pd

import params as P

FEATURES = ["recency", "history", "is_multichannel", "newbie"]
SEGMENT_COL = "segment"

# 類型 → (基礎轉換率 base, 真實增量 tau)
TYPE_EFFECTS = {
    "sure_thing": (0.85, 0.00),
    "persuadable": (0.10, 0.25),
    "lost_cause": (0.03, 0.00),
    "sleeping_dog": (0.35, -0.15),
}
TYPE_NAMES = list(TYPE_EFFECTS)


def make_synthetic(n=8000, seed=P.RANDOM_SEED):
    """生成 RCT 模擬資料：treatment 50/50 隨機，效果依隱藏類型異質。"""
    rng = np.random.default_rng(seed)
    recency = rng.integers(1, 13, n)  # 距上次消費月數
    history = np.round(rng.lognormal(4.0, 0.8, n), 2)  # 歷史消費金額
    is_multichannel = rng.integers(0, 2, n)
    newbie = rng.integers(0, 2, n)

    # 隱藏類型由可觀測特徵傾向性決定（含雜訊）→ 模型有機會間接學到
    active = recency <= 3
    mid = (recency > 3) & (recency <= 8)
    cold = recency > 8
    rich = history > np.quantile(history, 0.7)

    weights = np.full((n, 4), 0.05)  # 欄序同 TYPE_NAMES
    weights[active & rich, 0] += 0.80       # 近期高消費 → sure_thing
    weights[mid, 1] += 0.75                 # 中頻中值 → persuadable
    weights[cold & ~rich, 2] += 0.80        # 久未消費低額 → lost_cause
    weights[active & (is_multichannel == 1) & ~rich, 3] += 0.60  # sleeping_dog
    weights /= weights.sum(axis=1, keepdims=True)

    cum = np.cumsum(weights, axis=1)
    type_idx = (rng.random(n)[:, None] > cum).sum(axis=1)
    base = np.array([TYPE_EFFECTS[t][0] for t in TYPE_NAMES])[type_idx]
    tau = np.array([TYPE_EFFECTS[t][1] for t in TYPE_NAMES])[type_idx]

    treated = rng.integers(0, 2, n)  # RCT 50/50
    converted = rng.binomial(1, np.clip(base + tau * treated, 0.0, 1.0))

    df = pd.DataFrame(
        {
            "customer_id": np.arange(1, n + 1),
            "recency": recency,
            "history": history,
            "is_multichannel": is_multichannel,
            "newbie": newbie,
            "treated": treated,
            "converted": converted,
            "_true_type": np.array(TYPE_NAMES, dtype=object)[type_idx],
        }
    )
    df[SEGMENT_COL] = _make_segment(df)
    return df


def load_hillstrom():
    """載入 scripts/download_data.py 下載的 Hillstrom CSV，標準化為統一欄位。"""
    raw = pd.read_csv(P.HILLSTROM_CSV)
    df = pd.DataFrame(
        {
            "customer_id": np.arange(1, len(raw) + 1),
            "recency": raw["recency"],
            "history": raw["history"],
            "is_multichannel": (raw["channel"] == "Multichannel").astype(int),
            "newbie": raw["newbie"],
            # treatment：任一 email vs 無（2/3 treated，仍是隨機指派）
            "treated": (raw["segment"] != "No E-Mail").astype(int),
            "converted": raw[P.HILLSTROM_OUTCOME].astype(int),
        }
    )
    df[SEGMENT_COL] = _make_segment(df)
    return df


def load_data(synthetic=False, n=8000, seed=P.RANDOM_SEED):
    """回傳 (df, source_label)。無本地資料時自動退回 synthetic。"""
    if not synthetic and P.HILLSTROM_CSV.exists():
        return load_hillstrom(), "hillstrom"
    return make_synthetic(n=n, seed=seed), "synthetic"


def _make_segment(df):
    """客群 = recency 三分位 × history 三分位（9 格），用於覆蓋度護欄。"""
    r_bin = pd.qcut(df["recency"], 3, labels=["r1", "r2", "r3"], duplicates="drop")
    h_bin = pd.qcut(df["history"], 3, labels=["h1", "h2", "h3"], duplicates="drop")
    return r_bin.astype(str) + "_" + h_bin.astype(str)
