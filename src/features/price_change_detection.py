import numpy as np, pandas as pd

# detect price changes off a rolling-median baseline, then tag promo vs permanent

THRESH = 0.08      # min pct move to flag
MIN_DAYS = 3       # must persist this many selling days
REVERT_WINDOW = 14 # promo if it snaps back within this many days


def _smooth(s):
    return s.rolling(7, min_periods=1, center=False).median()


def detect_product(sub):
    sub = sub.sort_values("date").reset_index(drop=True)
    price = _smooth(sub["daily_price"]).to_numpy()
    dates = sub["date"].to_numpy()
    n = len(price)
    if n < MIN_DAYS + 2:
        return []

    events = []
    level = price[0]
    i = 1
    while i < n:
        move = (price[i] - level) / level if level else 0.0
        if abs(move) >= THRESH:
            # confirm it holds for MIN_DAYS
            j = i
            new_level = price[i]
            while j < n and abs((price[j] - level) / level) >= THRESH:
                j += 1
            if j - i >= MIN_DAYS:
                new_level = np.median(price[i:j])
                events.append({
                    "start": dates[i], "end": dates[min(j, n - 1)],
                    "old": round(float(level), 3), "new": round(float(new_level), 3),
                    "pct": round(float((new_level - level) / level), 4),
                })
                level = new_level
                i = j
                continue
        i += 1
    return events


def detect(daily):
    rows = []
    for name, sub in daily.groupby("product_name", sort=False):
        evs = detect_product(sub)
        prices = sub.sort_values("date")["daily_price"].to_numpy()
        for k, e in enumerate(evs):
            # reverting near the old level soon = promo
            nxt = evs[k + 1] if k + 1 < len(evs) else None
            dur = (pd.Timestamp(e["end"]) - pd.Timestamp(e["start"])).days
            reverts = nxt and abs(nxt["new"] - e["old"]) / e["old"] < 0.03 \
                and (pd.Timestamp(nxt["start"]) - pd.Timestamp(e["start"])).days <= REVERT_WINDOW
            kind = "promotion" if reverts else "permanent_change"
            note = "reverted within window" if reverts else "no revert seen"
            rows.append({
                "product_name": name,
                "start_date": pd.Timestamp(e["start"]).date(),
                "end_date": pd.Timestamp(e["end"]).date(),
                "old_price": e["old"], "new_price": e["new"],
                "pct_change": e["pct"], "event_type": kind,
                "confidence_notes": note,
            })
    return pd.DataFrame(rows, columns=[
        "product_name","start_date","end_date","old_price","new_price",
        "pct_change","event_type","confidence_notes"])
