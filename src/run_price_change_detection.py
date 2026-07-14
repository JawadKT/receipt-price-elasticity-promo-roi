from utils import load_receipts, daily_agg, tables
from features.price_change_detection import detect

if __name__ == "__main__":
    daily = daily_agg(load_receipts())
    ev = detect(daily)
    out = tables / "price_change_events.csv"
    ev.to_csv(out, index=False)
    print(f"{len(ev)} events ->", out)
    print(ev.to_string(index=False) if len(ev) else "(none)")
