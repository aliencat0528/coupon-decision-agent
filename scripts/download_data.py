"""下載 Hillstrom RCT 資料集到 data/hillstrom.csv（H1 接軌點：需網路）。

用法：
    .venv/bin/python scripts/download_data.py
    # 預期：saved 64000 rows -> .../data/hillstrom.csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
from sklift.datasets import fetch_hillstrom

import params as P


def main():
    P.DATA_DIR.mkdir(parents=True, exist_ok=True)
    bunch = fetch_hillstrom(target_col="all")
    df = pd.concat(
        [bunch.data, pd.DataFrame(bunch.target), pd.Series(bunch.treatment, name="segment")],
        axis=1,
    )
    df.to_csv(P.HILLSTROM_CSV, index=False)
    print(f"saved {len(df)} rows -> {P.HILLSTROM_CSV}")


if __name__ == "__main__":
    main()
