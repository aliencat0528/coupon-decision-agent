# coupon-decision-agent - 會拒絕決策的發券 Agent

對 6 萬名客戶逐一回答「該不該發折價券」，且在沒把握時**拒絕決策、轉人工**——
每筆決策附完整依據（uplift 信賴區間、期望值、理由、參數版本），可稽核。

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 功能特色 【必要】

- **Uplift 導向**：發券給 persuadables（有券才買），不是「最可能買的人」（propensity ≠ uplift）
- **三動作決策**：`ISSUE`（發）／`SKIP`（不發）／`ABSTAIN`（拒絕決策，轉人工審查）
- **風險感知拒絕**：EV 信賴區間跨 0 且最壞後悔值高於審查成本才拒絕；含預算與覆蓋度護欄
- **可稽核日誌**：`reports/decision_log.jsonl` 一列一決策，含 tau、CI、EV、reason、參數雜湊
- **RCT 回測**：holdout 上與 send_all／propensity_top／不拒絕版同場比較估計增量利潤

## 快速開始 【必要】

```bash
cd coupon-decision-agent
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python src/run_pipeline.py --synthetic --n 4000 --bootstrap 10
# 預期：依序印出 [1/5]～[5/5]，最後輸出決策分佈、政策比較表、Qini AUC，
#       並生成 REPORT.md 與 reports/decision_log.jsonl
```

## 使用方式 【必要】

- **完整跑（真資料）**：先 `.venv/bin/python scripts/download_data.py` 下載 Hillstrom（需網路），
  再 `.venv/bin/python src/run_pipeline.py`；沒有本地資料時自動退回 synthetic
- **調商業假設**：改 `src/params.py`（客單價、毛利、券面額、兌換率、審查成本、預算）後重跑，
  決策與報告自動更新；改動請記入 `prepare.md`
- **查單筆決策依據**：`grep '"customer_id": 123' reports/decision_log.jsonl | python3 -m json.tool`

## 專案結構 【必要】

```
src/
  params.py        # 商業假設與風險參數（單一真相來源）
  data.py          # Hillstrom 載入／synthetic RCT 生成（四類型隱藏客群）
  uplift.py        # scikit-uplift T-learner + bootstrap 信賴區間；propensity 基準
  decision.py      # 風險感知決策引擎（ISSUE / SKIP / ABSTAIN，兩類拒絕）
  audit.py         # JSONL 可稽核決策日誌
  backtest.py      # RCT holdout 政策比較與 Qini
  run_pipeline.py  # 一鍵編排
scripts/
  download_data.py # Hillstrom 下載（H1 接軌點）
```

## 測試 【必要】

```bash
.venv/bin/python src/run_pipeline.py --synthetic --n 4000 --bootstrap 10
```

## 版本歷史 【必要】

### v0.1.0 (2026-07-20)

- **MVP** — synthetic RCT 全 pipeline 跑通：uplift＋CI → 三動作決策 → 稽核日誌 → 回測報告

## 授權 【必要】

MIT License

---

## 相關文件

- 規劃書（觀念先修、商業考量、面試 Q&A）→ `prepare.md` 頂部連結
- 專案決策記錄 → `prepare.md`
