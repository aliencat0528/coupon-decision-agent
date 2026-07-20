# Prepare — coupon-decision-agent 決策記錄

> 記錄規則繼承根 `prepare.md`，此處只寫差異。編號前綴 `CA-`。
> 完整規劃書（觀念先修、商業考量、開發流程與出口條件、面試 Q&A）：（Artifact 連結待補）

---

## 決策日誌（新的在上）

### CA-003 · 2026-07-20
- **決策**：EV 口徑 = tau × 客單價 × 毛利率 − 券面額 × 兌換率；outcome 用 conversion
- **落地細節**：Hillstrom 落地時暫用 `visit`（conversion 僅 ~0.9% 太稀疏，見待討論 #2）；
  商業參數集中 `src/params.py`；LLM 不做數值預測（← D-001）

### CA-002 · 2026-07-20
- **決策**：決策空間三動作 `ISSUE` / `SKIP` / `ABSTAIN`；拒絕分兩類——
  護欄拒絕（覆蓋不足、預算耗盡）與統計拒絕（EV 信賴區間跨 0 且最小最壞後悔 > 審查成本）
- **理由**：對映 Appier Risk-Aware Decision Framework（答對獎勵／答錯懲罰／拒答成本）；
  低風險情境仍貪婪決策，避免「過度保守」這個框架論文指出的另一半毛病
- **棄選**：單一機率閾值拒絕（無金額語意）；只用點估計（表達不了「沒把握」）

### CA-001 · 2026-07-20 · ← D-001
- **決策**：工具鏈 scikit-uplift TwoModels + sklearn + bootstrap CI；
  主交付物 = 可稽核 `decision_log.jsonl` + `REPORT.md`（非 dashboard）
- **落地細節**：synthetic DGP（四類型隱藏客群）先驗證機制，Hillstrom 為第一個真資料；
  backtest 基準含 `propensity_top`，正面演示 propensity ≠ uplift
- **人為接軌點**：H1 Hillstrom 下載、H2 商業參數確認、H3 PR merge、
  H4 閾值校準（REVIEW_COST／CI 寬度敏感度）、H5 Criteo 放大與 Streamlit 部署（見規劃書）

---

## 待討論事項

| # | 議題 | 卡在什麼 | 提出日期 |
|---|------|---------|---------|
| 1 | REVIEW_COST 與 CI 百分位的校準 | 需 H4：對 ABSTAIN 率做敏感度分析後定案 | 2026-07-20 |
| 2 | Hillstrom outcome 用 visit 還是 conversion | conversion 太稀疏；visit 非金額事件，EV 口徑要重議 | 2026-07-20 |
| 3 | LLM 編排層（解釋、假設生成）何時加入 | MVP 不含；等 backtest 穩定後再議（規劃書 Phase 4） | 2026-07-20 |
