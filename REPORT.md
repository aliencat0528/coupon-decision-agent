# 發券決策 Agent — 執行報告

> run `1264a583` · 2026-07-20 09:03 · 資料來源：**synthetic**（⚠ 模擬資料，僅驗證機制，數字無商業意義）
> 參數版本 `13e283a00478` · train n=4800 · holdout n=3200

## 1. 決策分佈（依理由 × 動作）

| col_0                              |   ISSUE |   SKIP |   ABSTAIN |
|:-----------------------------------|--------:|-------:|----------:|
| confident_negative_ev              |       0 |   1189 |         0 |
| confident_positive_ev              |     744 |      0 |         0 |
| guardrail_budget_exhausted         |       0 |     33 |         0 |
| uncertain_low_stakes_greedy        |     327 |    361 |         0 |
| uncertain_regret_above_review_cost |       0 |      0 |       546 |

預算使用：2999 / 3000（期望券成本口徑）

## 2. 政策比較（RCT holdout 估計增量利潤）

| policy                   |   n_target |   inc_rate |   est_profit |
|:-------------------------|-----------:|-----------:|-------------:|
| agent（會拒絕）               |       1071 |     0.1742 |      1505.88 |
| uplift_top（同模型、不拒絕）      |       1071 |     0.172  |      2528.09 |
| propensity_top（發給最可能買的人） |       1071 |    -0.0131 |     -3418.15 |
| send_all（全發）             |       3200 |     0.0763 |     -1634.06 |
| send_none（全不發）           |          0 |     0      |        -0    |

- Qini AUC = **0.1049**（uplift 排序品質）
- 讀法：`propensity_top` 是天真做法「發給最可能買的人」——他們多半本來就會買，
  增量低、發券純虧；agent 的差異就是差在只發 persuadables、並在沒把握時拒絕。

## 3. 診斷（僅 synthetic：決策 × 隱藏真實類型）

| _true_type   |   ABSTAIN |   ISSUE |   SKIP |
|:-------------|----------:|--------:|-------:|
| lost_cause   |        96 |      61 |    728 |
| persuadable  |       225 |     897 |    207 |
| sleeping_dog |       100 |      56 |    350 |
| sure_thing   |       125 |      57 |    298 |

- 理想形狀：ISSUE 集中在 `persuadable`；`sure_thing`／`sleeping_dog` 被 SKIP；
  模型沒把握的落在 ABSTAIN。

## 4. 參數快照（商業假設，H2 接軌點）

|                     | value       |
|:--------------------|:------------|
| aov                 | 100.0       |
| gross_margin        | 0.3         |
| coupon_face         | 8.0         |
| redeem_rate         | 0.35        |
| review_cost         | 2.0         |
| budget_cap          | 3000.0      |
| min_segment_support | 150         |
| bootstrap_rounds    | 30          |
| ci_pct              | [5.0, 95.0] |

## 5. 限制與假設

- 客單價／毛利率／券成本／兌換率為商業判斷值，非資料推得；換參數需重跑並記錄。
- 券的效果以 email RCT 的 treatment 效果近似（Hillstrom 場景），外推到真發券需 A/B 驗證。
- 政策利潤是 holdout 上的統計估計，非實際帳務數字。
