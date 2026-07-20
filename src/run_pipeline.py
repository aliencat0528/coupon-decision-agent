"""一鍵跑完發券決策 agent：資料 → uplift＋CI → 逐客決策 → 稽核日誌 → 回測 → REPORT.md。

用法：
    python src/run_pipeline.py                         # 有 data/hillstrom.csv 用真資料，否則 synthetic
    python src/run_pipeline.py --synthetic             # 強制 synthetic
    python src/run_pipeline.py --n 4000 --bootstrap 10 # 快速煙霧測試

報告本文為繁中；決策日誌欄位為英文（機器可讀優先）。
"""

import argparse
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import params as P
from audit import AuditLog, params_hash, params_snapshot
from backtest import compare_policies, qini
from data import FEATURES, SEGMENT_COL, load_data
from decision import decide
from uplift import fit_propensity, fit_uplift_with_ci


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="發券決策 agent pipeline")
    parser.add_argument("--synthetic", action="store_true", help="強制使用 synthetic 資料")
    parser.add_argument("--n", type=int, default=8000, help="synthetic 樣本數")
    parser.add_argument("--bootstrap", type=int, default=P.BOOTSTRAP_ROUNDS,
                        help="bootstrap 次數（信賴區間來源）")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_id = uuid.uuid4().hex[:8]

    df, source = load_data(synthetic=args.synthetic, n=args.n)
    print(f"[1/5] 資料載入：{source}，n={len(df)}")

    train, holdout = train_test_split(
        df, test_size=P.TEST_SIZE, random_state=P.RANDOM_SEED, stratify=df["treated"]
    )
    holdout = holdout.reset_index(drop=True)
    support = train[SEGMENT_COL].value_counts()

    print(f"[2/5] 訓練 uplift（T-learner × bootstrap {args.bootstrap} 輪）…")
    tau_hat, tau_lo, tau_hi = fit_uplift_with_ci(
        train[FEATURES], train["converted"], train["treated"],
        holdout[FEATURES], rounds=args.bootstrap,
    )
    propensity = fit_propensity(train[FEATURES], train["converted"], holdout[FEATURES])

    print("[3/5] 逐客決策（期望值高者優先取用預算）…")
    audit = AuditLog(P.DECISION_LOG_PATH, run_id, source)
    decisions = np.empty(len(holdout), dtype=object)
    reasons = np.empty(len(holdout), dtype=object)
    budget_left = P.BUDGET_CAP
    for i in np.argsort(-tau_hat):
        row = holdout.iloc[i]
        rec = decide(tau_hat[i], tau_lo[i], tau_hi[i],
                     support.get(row[SEGMENT_COL], 0), budget_left)
        if rec["decision"] == "ISSUE":
            budget_left -= P.EXPECTED_COUPON_COST
        decisions[i], reasons[i] = rec["decision"], rec["reason"]
        audit.log_decision(
            {"customer_id": int(row["customer_id"]), "segment": str(row[SEGMENT_COL]), **rec}
        )
    audit.close()
    dec = pd.Series(decisions, index=holdout.index, name="decision")

    print("[4/5] RCT holdout 回測…")
    policy_table = compare_policies(holdout, dec, tau_hat, propensity)
    qini_score = qini(holdout["converted"], tau_hat, holdout["treated"])

    print("[5/5] 產出 REPORT.md …")
    _write_report(run_id, source, len(train), holdout, dec,
                  pd.Series(reasons, index=holdout.index), policy_table, qini_score, budget_left)

    print("\n== 決策分佈 ==")
    print(dec.value_counts().to_string())
    print("\n== 政策比較（估計增量利潤）==")
    print(policy_table.to_string(index=False))
    print(f"\nQini AUC = {qini_score:.4f}")
    print(f"報告：{P.REPORT_PATH}\n日誌：{P.DECISION_LOG_PATH}")


def _write_report(run_id, source, n_train, holdout, dec, reasons, policy_table, qini_score,
                  budget_left):
    counts = (
        pd.crosstab(dec, reasons).T.reindex(columns=["ISSUE", "SKIP", "ABSTAIN"], fill_value=0)
    )
    lines = [
        "# 發券決策 Agent — 執行報告",
        "",
        f"> run `{run_id}` · {datetime.now():%Y-%m-%d %H:%M} · 資料來源：**{source}**"
        + ("（⚠ 模擬資料，僅驗證機制，數字無商業意義）" if source == "synthetic" else ""),
        f"> 參數版本 `{params_hash()}` · train n={n_train} · holdout n={len(holdout)}",
        "",
        "## 1. 決策分佈（依理由 × 動作）",
        "",
        counts.to_markdown(),
        "",
        f"預算使用：{P.BUDGET_CAP - budget_left:.0f} / {P.BUDGET_CAP:.0f}（期望券成本口徑）",
        "",
        "## 2. 政策比較（RCT holdout 估計增量利潤）",
        "",
        policy_table.to_markdown(index=False),
        "",
        f"- Qini AUC = **{qini_score:.4f}**（uplift 排序品質）",
        "- 讀法：`propensity_top` 是天真做法「發給最可能買的人」——他們多半本來就會買，",
        "  增量低、發券純虧；agent 的差異就是差在只發 persuadables、並在沒把握時拒絕。",
        "",
    ]
    if "_true_type" in holdout.columns:
        diag = pd.crosstab(holdout["_true_type"], dec)
        lines += [
            "## 3. 診斷（僅 synthetic：決策 × 隱藏真實類型）",
            "",
            diag.to_markdown(),
            "",
            "- 理想形狀：ISSUE 集中在 `persuadable`；`sure_thing`／`sleeping_dog` 被 SKIP；",
            "  模型沒把握的落在 ABSTAIN。",
            "",
        ]
    snapshot = params_snapshot()
    lines += [
        "## 4. 參數快照（商業假設，H2 接軌點）",
        "",
        pd.Series(snapshot, dtype=object).to_frame("value").to_markdown(),
        "",
        "## 5. 限制與假設",
        "",
        "- 客單價／毛利率／券成本／兌換率為商業判斷值，非資料推得；換參數需重跑並記錄。",
        "- 券的效果以 email RCT 的 treatment 效果近似（Hillstrom 場景），外推到真發券需 A/B 驗證。",
        "- 政策利潤是 holdout 上的統計估計，非實際帳務數字。",
        "",
    ]
    P.REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
