"""Run promotion ROI simulation using elasticity estimates.

Usage (from repo root):

    python src/run_promo_simulation.py

This script:
- Loads `data/sample/synthetic_receipts.csv`.
- Loads `reports/tables/elasticity_estimates.csv`.
- Computes, for each product, baseline_price and baseline_daily_qty as:
    * baseline_price: median unit_price over the most recent 14 days
    * baseline_daily_qty: average daily quantity over the most recent 14 days
- Joins with elasticity estimates (on product_name).
- Runs promo scenarios for discount levels [5%, 10%, 15%, 20%]
  for products that have elasticity estimates.
- Writes `reports/tables/promo_scenarios.csv`.

If no scenarios can be generated (e.g., no elasticity estimates), an
empty CSV with headers is still written.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from features.promo_roi import simulate_promo_scenarios


def compute_baseline_metrics(df: pd.DataFrame, window_days: int = 14) -> pd.DataFrame:
    """Compute baseline price and daily quantity over the most recent window.

    Parameters
    ----------
    df : DataFrame
        Must include columns [timestamp, product_name, quantity, unit_price].
    window_days : int
        Number of days to look back from the latest date in the data.

    Returns
    -------
    DataFrame
        Columns: product_name, baseline_price, baseline_daily_qty.
    """

    required = {"timestamp", "product_name", "quantity", "unit_price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input data missing required columns: {sorted(missing)}")

    tmp = df.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"])
    tmp["date"] = tmp["timestamp"].dt.date

    max_date = tmp["date"].max()
    if pd.isna(max_date):
        raise ValueError("No dates found in input data")

    max_ts = pd.to_datetime(max_date)
    cutoff = max_ts - pd.Timedelta(days=window_days - 1)

    window_df = tmp[tmp["timestamp"] >= cutoff].copy()
    window_df["date"] = window_df["timestamp"].dt.date

    # Daily aggregation per product
    daily = (
        window_df.groupby(["product_name", "date"], as_index=False)
        .agg(
            daily_qty=("quantity", "sum"),
            daily_price=("unit_price", "median"),
        )
    )

    # Baseline over the window
    baseline = (
        daily.groupby("product_name", as_index=False)
        .agg(
            baseline_daily_qty=("daily_qty", "mean"),
            baseline_price=("daily_price", "median"),
        )
    )

    return baseline


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    data_path = repo_root / "data" / "sample" / "synthetic_receipts.csv"
    elasticity_path = repo_root / "reports" / "tables" / "elasticity_estimates.csv"
    out_dir = repo_root / "reports" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "promo_scenarios.csv"

    print(f"Loading receipts from {data_path} ...")
    df = pd.read_csv(data_path)

    print(f"Loading elasticity estimates from {elasticity_path} ...")
    if elasticity_path.exists():
        elasticity_df = pd.read_csv(elasticity_path)
    else:
        print("Elasticity estimates file not found; proceeding with empty estimates.")
        elasticity_df = pd.DataFrame(
            columns=[
                "product_name",
                "elasticity",
                "ci_low",
                "ci_high",
                "p_value",
                "n_days",
                "unique_prices",
                "r2",
            ]
        )

    if elasticity_df.empty:
        print("No elasticity estimates available; writing empty promo_scenarios.csv.")
        empty = simulate_promo_scenarios(
            pd.DataFrame(
                columns=[
                    "product_name",
                    "baseline_price",
                    "baseline_daily_qty",
                    "elasticity",
                    "unit_cost",
                ]
            )
        )
        empty.to_csv(out_path, index=False)
        print(f"Promo scenarios written to {out_path} (empty, no elasticity estimates).")
        return

    # Compute baseline metrics over recent window
    print("Computing baseline price and quantity over recent 14-day window ...")
    baseline = compute_baseline_metrics(df, window_days=14)

    # Merge baseline with elasticity estimates
    merged = baseline.merge(elasticity_df[["product_name", "elasticity"]], on="product_name", how="inner")

    if merged.empty:
        print("No overlap between baseline products and elasticity estimates; writing empty file.")
        simulate_promo_scenarios(
            pd.DataFrame(
                columns=[
                    "product_name",
                    "baseline_price",
                    "baseline_daily_qty",
                    "elasticity",
                ]
            )
        ).to_csv(out_path, index=False)
        print(f"Promo scenarios written to {out_path} (empty, no matched products).")
        return

    # Optionally restrict to top 10 products by revenue among those with elasticity
    revenue = (
        df.groupby("product_name", as_index=False)["line_total"]
        .sum()
        .sort_values("line_total", ascending=False)
    )
    candidates = revenue["product_name"].tolist()

    # Keep products that both have elasticity and are top sellers
    merged["_rank"] = merged["product_name"].apply(lambda p: candidates.index(p) if p in candidates else len(candidates))
    merged = merged.sort_values("_rank").drop(columns=["_rank"])
    top_10_names = merged["product_name"].head(10).tolist()
    merged_top = merged[merged["product_name"].isin(top_10_names)].copy()

    print("Products included in promo simulation:")
    for name in top_10_names:
        print(f"  - {name}")

    # Add unit_cost column placeholder (not available in synthetic data)
    merged_top["unit_cost"] = pd.NA

    inputs = merged_top[["product_name", "baseline_price", "baseline_daily_qty", "elasticity", "unit_cost"]]

    print("Running promo ROI scenarios ...")
    scenarios = simulate_promo_scenarios(inputs)

    scenarios.to_csv(out_path, index=False)
    print(f"Promo scenarios written to {out_path}.")


if __name__ == "__main__":
    main()
