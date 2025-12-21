"""Run baseline price elasticity estimation from receipt data.

Usage (from repo root):

    python src/run_elasticity.py

This script:
- Loads `data/sample/synthetic_receipts.csv` with pandas.
- Identifies the top 20 products by revenue (line_total).
- Runs per-product log-log elasticity estimation with DOW controls.
- Writes `reports/tables/elasticity_estimates.csv` for the
  successfully estimated products.

Most elasticities are expected to be negative (downward-sloping demand),
but not necessarily all.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from features.elasticity_model import estimate_elasticity_per_product


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data" / "sample" / "synthetic_receipts.csv"
    out_dir = repo_root / "reports" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "elasticity_estimates.csv"

    print(f"Loading data from {data_path} ...")
    df = pd.read_csv(data_path)

    # Ensure required columns exist
    required_cols = {"timestamp", "product_name", "quantity", "unit_price", "line_total"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Input data missing required columns: {sorted(missing)}")

    # Top 20 products by revenue
    revenue = (
        df.groupby("product_name", as_index=False)["line_total"]
        .sum()
        .sort_values("line_total", ascending=False)
    )
    top_products = revenue["product_name"].head(20).tolist()

    print("Top products by revenue (up to 20):")
    for p in top_products:
        print(f"  - {p}")

    df_top = df[df["product_name"].isin(top_products)].copy()

    print("Running elasticity estimation per product ...")
    estimates, skipped = estimate_elasticity_per_product(df_top)

    if estimates.empty:
        print("No products met minimum data criteria for elasticity estimation.")
        # Still write an empty CSV with headers
        estimates.to_csv(out_path, index=False)
    else:
        print(f"Estimated elasticity for {len(estimates)} products.")
        estimates.to_csv(out_path, index=False)

    if not skipped.empty:
        print("Some products were skipped (sparse or problematic):")
        print(skipped.to_string(index=False))

    print(f"Elasticity estimates written to {out_path}.")


if __name__ == "__main__":
    main()
