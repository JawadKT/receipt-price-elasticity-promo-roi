import numpy as np, pandas as pd
from pathlib import Path

# builds synthetic grocery receipts w/ known elasticity + 2 promos + 1 permanent price hike
# prices move in piecewise-constant steps so the log-log model can actually identify beta

seed = 7
rng = np.random.default_rng(seed)

out = Path(__file__).resolve().parents[1] / "data" / "sample" / "synthetic_receipts.csv"

# name, category, base_price, true_elasticity, base_daily_qty
products = [
    ("milk 2L", "dairy", 3.20, -0.6, 34),
    ("eggs dozen", "dairy", 4.10, -0.9, 28),
    ("butter", "dairy", 5.50, -1.3, 18),
    ("cheddar 200g", "dairy", 4.80, -1.1, 20),
    ("bananas kg", "produce", 1.40, -0.7, 42),
    ("apples kg", "produce", 2.30, -0.8, 30),
    ("tomatoes kg", "produce", 3.10, -1.2, 24),
    ("spinach bag", "produce", 2.60, -1.4, 18),
    ("chicken breast kg", "meat", 9.20, -1.0, 22),
    ("ground beef kg", "meat", 8.10, -1.1, 20),
    ("bacon 400g", "meat", 6.40, -1.6, 16),
    ("white bread", "bakery", 2.20, -0.8, 32),
    ("bagels 6pk", "bakery", 3.30, -1.2, 18),
    ("croissant 4pk", "bakery", 4.20, -1.7, 14),
    ("orange juice 1L", "beverage", 3.90, -1.3, 20),
    ("coffee 500g", "beverage", 11.50, -0.9, 15),
    ("cola 2L", "beverage", 2.50, -1.5, 26),
    ("pasta 500g", "pantry", 1.80, -0.7, 28),
    ("rice 1kg", "pantry", 3.40, -0.6, 22),
    ("olive oil 1L", "pantry", 12.90, -1.0, 12),
    ("cereal 500g", "pantry", 4.60, -1.2, 18),
    ("yogurt 4pk", "dairy", 3.70, -1.1, 20),
]

days = 50
start = pd.Timestamp("2025-01-06")
dates = [start + pd.Timedelta(days=i) for i in range(days)]
dow_lift = {0:0.95,1:0.92,2:0.98,3:1.02,4:1.15,5:1.30,6:1.10}  # weekend bump

promo_prods = ["bacon 400g", "croissant 4pk"]   # temp drops
perm_prod = "milk 2L"                            # permanent hike


def price_path(base):
    # piecewise price segments within +/-12% of base
    p = np.empty(days)
    i = 0
    while i < days:
        seg = int(rng.integers(6, 11))
        lvl = round(base * rng.uniform(0.88, 1.12), 2)
        p[i:i + seg] = lvl
        i += seg
    return p


rows = []
tid = 0
for name, cat, base, elast, base_qty in products:
    prices = price_path(base)
    for i, d in enumerate(dates):
        price = float(prices[i])
        if name in promo_prods and 20 <= i < 27:
            price = round(base * 0.80, 2)           # ~20% off for a week
        if name == perm_prod and i >= 28:
            price = round(base * 1.12, 2)           # permanent +12%
        price = max(price, 0.5)

        mult = (price / base) ** elast
        lam = base_qty * mult * dow_lift[d.dayofweek] * rng.lognormal(0, 0.06)
        q = int(rng.poisson(max(lam, 0.1)))
        if q <= 0:
            continue

        n_lines = int(rng.integers(1, 4))
        cuts = sorted(rng.choice(range(1, q + 1), size=min(n_lines, q), replace=False)) if q > 1 else [1]
        prev = 0
        for c in cuts:
            qty = c - prev
            prev = c
            if qty <= 0:
                continue
            ts = d + pd.Timedelta(hours=int(rng.integers(8, 21)), minutes=int(rng.integers(0, 60)))
            rows.append((f"T{tid:05d}", ts, name, cat, qty, price, round(qty * price, 2)))
            tid += 1

df = pd.DataFrame(rows, columns=["transaction_id","timestamp","product_name","category","quantity","unit_price","line_total"])
df = df.sort_values("timestamp").reset_index(drop=True)
df.to_csv(out, index=False)
print("wrote", out, df.shape)
