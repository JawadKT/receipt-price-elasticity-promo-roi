import pandas as pd
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sample = root / "data" / "sample"
tables = root / "reports" / "tables"


def load_receipts(path=None, name_map=None):
    # default to bundled synthetic file
    path = Path(path) if path else sample / "synthetic_receipts.csv"
    df = pd.read_csv(path, parse_dates=["timestamp"])

    # optional raw->canonical name mapping
    mp = Path(name_map) if name_map else sample / "product_name_map.csv"
    if mp.exists():
        m = pd.read_csv(mp)
        df = df.merge(m, left_on="product_name", right_on="raw_name", how="left")
        df["product_name"] = df["canonical_name"].fillna(df["product_name"])
        df["category"] = df["category_y"].fillna(df["category_x"]) if "category_y" in df else df["category"]
        df = df[["transaction_id","timestamp","product_name","category","quantity","unit_price","line_total"]]

    df["date"] = df["timestamp"].dt.normalize()
    return df


def daily_agg(df):
    # daily median price + total qty per product (vectorized)
    g = df.groupby(["product_name", "date"], sort=False)
    out = g.agg(daily_price=("unit_price", "median"), daily_qty=("quantity", "sum")).reset_index()
    return out.sort_values(["product_name", "date"]).reset_index(drop=True)
