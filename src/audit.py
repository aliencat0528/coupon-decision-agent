"""可稽核決策日誌：JSONL，一列一決策，含完整依據與參數快照。

「可稽核的決策日誌，不是 dashboard」是本專案的主交付物（← D-001）。
任何一筆 ISSUE / SKIP / ABSTAIN 都要能回答三件事：
當時模型看到什麼（tau 與信賴區間）、依哪條規則（reason）、參數是哪一版（params_hash）。
"""

import hashlib
import json
from datetime import datetime, timezone

import params as P


def params_snapshot():
    """商業與風險參數快照——決策的「當時條件」，隨每個 run 寫進日誌。"""
    return {
        "aov": P.AOV,
        "gross_margin": P.GROSS_MARGIN,
        "coupon_face": P.COUPON_FACE,
        "redeem_rate": P.REDEEM_RATE,
        "review_cost": P.REVIEW_COST,
        "budget_cap": P.BUDGET_CAP,
        "min_segment_support": P.MIN_SEGMENT_SUPPORT,
        "bootstrap_rounds": P.BOOTSTRAP_ROUNDS,
        "ci_pct": [P.CI_LO_PCT, P.CI_HI_PCT],
    }


def params_hash():
    blob = json.dumps(params_snapshot(), sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class AuditLog:
    """JSONL 決策日誌。第一列是 run_meta，之後每列一筆 decision。"""

    def __init__(self, path, run_id, data_source):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "w", encoding="utf-8")
        self.run_id = run_id
        self._write(
            {
                "kind": "run_meta",
                "run_id": run_id,
                "ts": _now(),
                "data_source": data_source,
                "params_hash": params_hash(),
                "params": params_snapshot(),
            }
        )

    def log_decision(self, record):
        self._write({"kind": "decision", "run_id": self.run_id, "ts": _now(), **record})

    def close(self):
        self._fh.close()

    def _write(self, obj):
        self._fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
