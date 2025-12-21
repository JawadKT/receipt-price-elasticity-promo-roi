"""Run price-change & promo detection on synthetic receipt data.

Usage (from repo root):

    python src/run_price_change_detection.py

This script:
- Loads `data/sample/synthetic_receipts.csv` with pandas.
- Calls the detector in `src/features/price_change_detection.py`.
- Writes `reports/tables/price_change_events.csv`.
- Prints a short summary to the console.

If no events are detected, it still writes an empty CSV with just headers
and prints a note to the console.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from features.price_change_detection import detect_price_change_events


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data" / "sample" / "synthetic_receipts.csv"
    out_dir = repo_root / "reports" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "price_change_events.csv"

    print(f"Loading data from {data_path} ...")
    df = pd.read_csv(data_path)

    print("Running price change detection ...")
    events_df = detect_price_change_events(df)

    if events_df.empty:
        print("No price change events detected. Writing empty file with headers only.")
        # Ensure correct columns / headers even if empty
        events_df.to_csv(out_path, index=False)
    else:
        print(f"Detected {len(events_df)} events. Writing to {out_path} ...")
        events_df.to_csv(out_path, index=False)

    print("Done.")


if __name__ == "__main__":
    main()
