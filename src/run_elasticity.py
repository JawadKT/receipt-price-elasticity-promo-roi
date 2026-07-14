from utils import load_receipts, daily_agg, tables
from features.elasticity_model import estimate

if __name__ == "__main__":
    daily = daily_agg(load_receipts())
    est = estimate(daily)
    out = tables / "elasticity_estimates.csv"
    est.to_csv(out, index=False)
    print(f"{len(est)} products modeled ->", out)
    print(est.to_string(index=False) if len(est) else "(none met thresholds)")
