> 繼承根目錄共用規則（Claude Code 已自動載入，勿重複讀取 ../CLAUDE.md）

# coupon-decision-agent

作品集專案一：會拒絕決策的發券 Agent（Appier AiDeal ＋ Risk-Aware Decision Framework 對映）。
主軸：**每個分析結論都接一個金額化決策**；差異化是 agent「知道自己何時不該決定」。
規劃書見 prepare.md 頂部連結。

## 技術棧與指令

- Python 3.12 + venv（`.venv/`），依賴見 `requirements.txt`
- uplift：scikit-uplift 現成 meta-learner（TwoModels / T-learner），**不手刻演算法**
- 資料下載：`.venv/bin/python scripts/download_data.py`（Hillstrom，需網路；H1 接軌點）
- 一鍵跑 pipeline：`.venv/bin/python src/run_pipeline.py`（無資料時自動退回 `--synthetic`）
  輸出 `REPORT.md`（進版控）與 `reports/decision_log.jsonl`（不進版控）
- 煙霧測試：`.venv/bin/python src/run_pipeline.py --synthetic --n 4000 --bootstrap 10`

## 專案規則（與根規則的差異）

- `data/` 與 `reports/` 不進 git；原始 CSV 唯讀
- **LLM 不做數值預測**：所有數值出自 uplift 層統計模型；LLM（後期 Phase）只做解釋與編排
- 決策動作只有三種：`ISSUE` / `SKIP` / `ABSTAIN`；每筆決策必須寫入
  `reports/decision_log.jsonl` 並含 tau、信賴區間、EV、reason、params_hash（可稽核是主交付物）
- 兩類拒絕不可混用：護欄拒絕（guardrail_*，確定性）與統計拒絕（uncertain_*，不確定性）
- 商業假設參數（客單價、毛利率、券面額、兌換率、審查成本、預算）集中 `src/params.py`，
  改參數不改邏輯；門檻或口徑改動必須記入 `prepare.md`
