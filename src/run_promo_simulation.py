import pandas as pd
from utils import load_receipts, daily_agg, tables
from features.elasticity_model import estimate
from features.promo_roi import run

TOP_N = 8          # top products by revenue
BASELINE_DAYS = 14


def baselines(df, daily):
    last = daily.date.max() - pd.Timedelta(days=BASELINE_DAYS)
    recent = daily[daily.date > last]
    b = recent.groupby("product_name").agg(
        baseline_price=("daily_price", "median"),
        baseline_daily_qty=("daily_qty", "mean")).reset_index()
    # rank by total revenue, keep top n
    rev = df.groupby("product_name").line_total.sum().sort_values(ascending=False)
    keep = rev.head(TOP_N).index
    return b[b.product_name.isin(keep)]


if __name__ == "__main__":
    df = load_receipts()
    daily = daily_agg(df)
    est = estimate(daily)
    est = est[est.elasticity < 0]        # own-price elasticity must be negative to be valid
    b = baselines(df, daily)
    res = run(b, est)
    out = tables / "promo_scenarios.csv"
    res.to_csv(out, index=False)
    print(f"{res.product_name.nunique() if len(res) else 0} products x {len(res)} rows ->", out)
    print(res.to_string(index=False) if len(res) else "(no overlap with elasticity)")
