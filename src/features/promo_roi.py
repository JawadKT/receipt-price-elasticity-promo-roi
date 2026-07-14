import numpy as np, pandas as pd

# simulate revenue/profit change at fixed discount depths given elasticity

DISCOUNTS = [0.05, 0.10, 0.15, 0.20]


def scenarios(baseline_price, baseline_daily_qty, elasticity, unit_cost=np.nan):
    d = np.array(DISCOUNTS)
    new_price = baseline_price * (1 - d)
    exp_qty = baseline_daily_qty * (new_price / baseline_price) ** elasticity
    exp_rev = new_price * exp_qty
    base_rev = baseline_price * baseline_daily_qty
    out = pd.DataFrame({
        "discount_pct": (d * 100).astype(int),
        "new_price": new_price.round(3),
        "expected_qty": exp_qty.round(2),
        "expected_revenue": exp_rev.round(2),
        "baseline_revenue": round(float(base_rev), 2),
        "revenue_change": (exp_rev - base_rev).round(2),
    })
    if not np.isnan(unit_cost):
        base_profit = (baseline_price - unit_cost) * baseline_daily_qty
        exp_profit = (new_price - unit_cost) * exp_qty
        out["baseline_profit"] = round(float(base_profit), 2)
        out["expected_profit"] = exp_profit.round(2)
        out["profit_change"] = (exp_profit - base_profit).round(2)
    return out


def run(baselines, elast):
    # baselines: product_name, baseline_price, baseline_daily_qty, [unit_cost]
    m = baselines.merge(elast[["product_name", "elasticity"]], on="product_name", how="inner")
    frames = []
    for _, r in m.iterrows():
        s = scenarios(r.baseline_price, r.baseline_daily_qty, r.elasticity,
                      r.get("unit_cost", np.nan))
        s.insert(0, "product_name", r.product_name)
        s.insert(2, "elasticity", r.elasticity)
        frames.append(s)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
