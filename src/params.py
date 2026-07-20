"""全專案參數的單一真相來源。

商業假設區（H2 人為接軌點）：Hillstrom 資料沒有成本欄位，
客單價／毛利率／券面額／兌換率／審查成本／預算全是商業判斷值——
改完數字重跑 pipeline，決策與報告自動更新。改動口徑必須記入 prepare.md。
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
DECISION_LOG_PATH = REPORTS_DIR / "decision_log.jsonl"
REPORT_PATH = PROJECT_ROOT / "REPORT.md"
HILLSTROM_CSV = DATA_DIR / "hillstrom.csv"

# ── 商業假設（標明「假設」，非資料推得；H2 接軌點）──────────────
AOV = 100.0            # 平均客單價（USD）
GROSS_MARGIN = 0.30    # 毛利率
COUPON_FACE = 8.0      # 券面額（USD）
REDEEM_RATE = 0.35     # 發出後被實際使用的比率
REVIEW_COST = 2.0      # ABSTAIN 轉人工審查的單件成本（USD）
BUDGET_CAP = 3000.0    # 活動預算上限：期望券成本累計（USD）

# 發一張券的期望成本（只在被兌換時才付出面額）
EXPECTED_COUPON_COST = COUPON_FACE * REDEEM_RATE

# ── 風險決策參數 ────────────────────────────────────────────
MIN_SEGMENT_SUPPORT = 150  # 訓練集中該客群樣本數低於此值 → 護欄 ABSTAIN（覆蓋不足）
BOOTSTRAP_ROUNDS = 30      # bootstrap 重抽次數（uplift 信賴區間來源）
CI_LO_PCT = 5.0            # 區間下界百分位
CI_HI_PCT = 95.0           # 區間上界百分位

# ── 資料與重現性 ────────────────────────────────────────────
RANDOM_SEED = 42
TEST_SIZE = 0.4            # RCT holdout 比例（決策與 backtest 都在 holdout 上做）

# Hillstrom 的 conversion 只有 ~0.9%，MVP 先用 visit 當 outcome（待討論 #2）
HILLSTROM_OUTCOME = "visit"
