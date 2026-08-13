# Prepare — coupon-decision-agent 決策記錄

> **版本**：CA-004 · 2026-07-21
> 記錄規則繼承根 `prepare.md`，此處只寫差異。編號前綴 `CA-`。
> 完整規劃書（觀念先修、商業考量、開發流程與出口條件、面試 Q&A）：
> https://claude.ai/code/artifact/c58198fe-d276-47bd-a527-1e08a1a693dd

---

## 決策日誌（新的在上）

### CA-004 · 2026-07-21 · outcome 口徑定案（← 待討論 #2 結案）
> ⚠️ **歸屬訂正（2026-08-02）**：本筆原記為「用戶拍板」，**訂正為「用戶確認採建議」**。
> 用戶於 2026-08-02 表示對此決定沒有印象，三個選項的取捨理由是 AI 提出的。
> 訂正的是歸屬，不是決策本身——`spend` 這個選擇與下方理由仍然成立，只是**還沒有人真的複核過**。
> 待用戶理解三個 outcome 的取捨後再回來確認或推翻（見根目錄 `portfolio.md` 的「還不懂」第 4 條）。

- **決策**（用戶確認採建議）：uplift outcome 用 `spend`（連續金額）——非 visit（15% 但非金額事件、
  需一個沒估過的「造訪→購買」代理）、非 conversion（0.9% 太稀疏，逐人 CI 幾乎全跨零→近乎全 ABSTAIN）
- **EV 口徑修正 CA-003**：`tau_spend × 毛利率 − 券面額 × 兌換率`；tau 改吃 spend、不再乘固定客單價
- **落地細節**（排專案一深化時段，非現在）：uplift 換 regressor T-learner；conversion 留作報告次要
  outcome 佐證方向；spend 零膨脹較吵 → 靠 bootstrap CI，吵的自然落 ABSTAIN

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
| ~~2~~ | ~~Hillstrom outcome 用 visit 還是 conversion~~ | 已結案 → CA-004 定為 `spend` | 2026-07-20 |
| 3 | LLM 編排層（解釋、假設生成）何時加入 | MVP 不含；等 backtest 穩定後再議（規劃書 Phase 4） | 2026-07-20 |
