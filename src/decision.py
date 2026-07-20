"""風險感知決策引擎——Appier Risk-Aware Decision Framework 的對映實作。

三動作：ISSUE（發券）／SKIP（不發）／ABSTAIN（拒絕決策，轉人工）。
兩類拒絕，稽核時要分開看：
  1. 護欄拒絕（確定性）：客群覆蓋不足、預算耗盡——不是模型不確定，是規則不允許
  2. 統計拒絕（不確定性）：EV 信賴區間跨 0，且無論賭哪邊，最壞情況的後悔值
     都高於人工審查成本 → 花 REVIEW_COST 買資訊比亂猜便宜

對映框架：答對獎勵＝增量毛利、答錯懲罰＝券成本或錯失毛利、拒答成本＝REVIEW_COST。
"""

import params as P


def expected_value(tau):
    """發券的單客期望增量利潤 = 增量轉換率 × 客單價 × 毛利率 − 期望券成本。"""
    return tau * P.AOV * P.GROSS_MARGIN - P.EXPECTED_COUPON_COST


def decide(tau_hat, tau_lo, tau_hi, support, budget_left):
    """單客決策。回傳含決策、理由與完整依據的 dict（直接進稽核日誌）。"""
    ev_hat = expected_value(tau_hat)
    ev_lo = expected_value(tau_lo)
    ev_hi = expected_value(tau_hi)
    base = {
        "tau_hat": round(float(tau_hat), 4),
        "tau_lo": round(float(tau_lo), 4),
        "tau_hi": round(float(tau_hi), 4),
        "ev_hat": round(float(ev_hat), 2),
        "ev_lo": round(float(ev_lo), 2),
        "ev_hi": round(float(ev_hi), 2),
        "segment_support": int(support),
        "budget_left": round(float(budget_left), 2),
    }

    # 1) 覆蓋度護欄（確定性）：模型在這個客群根本沒學過，任何估計都不可信
    if support < P.MIN_SEGMENT_SUPPORT:
        return {**base, "decision": "ABSTAIN", "reason": "guardrail_insufficient_support"}

    # 2) 統計判斷
    if ev_lo > 0:
        action, reason = "ISSUE", "confident_positive_ev"
    elif ev_hi < 0:
        action, reason = "SKIP", "confident_negative_ev"
    else:
        # 區間跨 0：後悔值分析
        regret_issue = -ev_lo  # 發了、但真實 EV 落在下界 → 最壞損失
        regret_skip = ev_hi    # 不發、但真實 EV 落在上界 → 最壞錯失
        if min(regret_issue, regret_skip) > P.REVIEW_COST:
            return {**base, "decision": "ABSTAIN", "reason": "uncertain_regret_above_review_cost"}
        # 賭錯也便宜 → 依點估計貪婪決策（低風險情境不該過度保守，框架論文的另一半）
        action = "ISSUE" if ev_hat > 0 else "SKIP"
        reason = "uncertain_low_stakes_greedy"

    # 3) 預算護欄（確定性）：只攔「本來要發」的決策，不蓋掉其他理由
    if action == "ISSUE" and budget_left < P.EXPECTED_COUPON_COST:
        return {**base, "decision": "SKIP", "reason": "guardrail_budget_exhausted"}
    return {**base, "decision": action, "reason": reason}
