"""Price change and promotion detection utilities.

This module provides a simple, defensible MVP for detecting price change
and promo events from receipt line-item data.

Input schema expectation (per row):
- transaction_id
- timestamp (parseable to datetime)
- product_name
- category
- quantity
- unit_price
- line_total

High-level approach
-------------------
1. Aggregate to daily median unit_price and daily total quantity per product.
2. Smooth median price with a 7-day rolling median (per product).
3. Detect change points where the smoothed price moves by >= 8%% relative
   to the prior "stable" level and persists for >= 3 consecutive selling days.
4. Classify each event as:
   - "promotion" if the price reverts to (approximately) the old level
     within 14 days.
   - "permanent_change" otherwise.

Outputs a DataFrame with:
- product_name
- start_date
- end_date
- old_price
- new_price
- pct_change
- event_type ("promotion" | "permanent_change")
- confidence_notes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd


@dataclass
class PriceChangeEvent:
    product_name: str
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    old_price: float
    new_price: float
    pct_change: float
    event_type: str
    confidence_notes: str


def _prepare_daily_price(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw line-items to daily median price and total quantity.

    Returns a DataFrame with columns:
    - product_name
    - date
    - median_price
    - total_qty
    - smooth_price (7-day rolling median of median_price)
    """

    if "timestamp" not in df.columns:
        raise ValueError("Expected 'timestamp' column in data frame")

    local_df = df.copy()
    local_df["timestamp"] = pd.to_datetime(local_df["timestamp"])
    local_df["date"] = local_df["timestamp"].dt.date

    daily = (
        local_df.groupby(["product_name", "date"], as_index=False)
        .agg(
            median_price=("unit_price", "median"),
            total_qty=("quantity", "sum"),
        )
        .sort_values(["product_name", "date"])
    )

    # Apply 7-day rolling median per product
    def _roll(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values("date").copy()
        group["smooth_price"] = (
            group["median_price"].rolling(window=7, min_periods=1).median()
        )
        return group

    daily = daily.groupby("product_name", group_keys=False).apply(_roll)
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def _detect_events_for_product(
    pdf: pd.DataFrame,
    product_name: str,
    min_rel_change: float = 0.08,
    min_persist_days: int = 3,
    revert_window_days: int = 14,
    revert_tolerance: float = 0.03,
) -> List[PriceChangeEvent]:
    """Detect price change events for a single product's time series.

    Parameters
    ----------
    pdf : DataFrame
        Must contain columns ["date", "smooth_price", "median_price"].
    product_name : str
        Name of the product for reporting.
    min_rel_change : float
        Minimum relative change (e.g., 0.08 for 8%%) to consider a change.
    min_persist_days : int
        Minimum number of consecutive selling days at the new level.
    revert_window_days : int
        If the price returns near the old level within this window, we
        classify as a promotion.
    revert_tolerance : float
        Relative tolerance to consider the price as "reverted".
    """

    if pdf.empty:
        return []

    pdf = pdf.sort_values("date").reset_index(drop=True)

    dates = pdf["date"].to_numpy()
    prices = pdf["smooth_price"].to_numpy(dtype=float)

    events: List[PriceChangeEvent] = []

    # Start with first non-null price as the initial stable level.
    if np.isnan(prices).all():
        return []

    current_level = float(prices[~np.isnan(prices)][0])
    stable_idx = 0

    i = 1
    n = len(pdf)
    while i < n:
        price = prices[i]
        if np.isnan(price):
            i += 1
            continue

        rel_change = (price - current_level) / current_level if current_level else 0.0

        if abs(rel_change) < min_rel_change:
            # Still considered part of the stable regime.
            current_level = (current_level + price) / 2.0
            stable_idx = i
            i += 1
            continue

        # Potential change: require persistence for min_persist_days.
        change_sign = np.sign(rel_change)
        start_idx = i
        j = i
        consecutive = 0
        while j < n:
            pj = prices[j]
            if np.isnan(pj):
                break
            rel_j = (pj - current_level) / current_level if current_level else 0.0
            if np.sign(rel_j) == change_sign and abs(rel_j) >= min_rel_change:
                consecutive += 1
                j += 1
            else:
                break

        if consecutive < min_persist_days:
            # Not persistent enough; treat as noise.
            i += 1
            continue

        # We have a candidate regime starting at start_idx up to j-1.
        new_level = float(np.nanmedian(prices[start_idx:j]))
        start_date = dates[start_idx]

        # Look forward for reversion within revert_window_days.
        promo_end_idx = j - 1
        revert_found = False
        revert_deadline = dates[start_idx] + np.timedelta64(revert_window_days, "D")

        k = j
        while k < n and dates[k] <= revert_deadline:
            pk = prices[k]
            if np.isnan(pk):
                k += 1
                continue
            rel_back = (pk - current_level) / current_level if current_level else 0.0
            if abs(rel_back) <= revert_tolerance:
                revert_found = True
                promo_end_idx = k - 1 if k - 1 >= start_idx else start_idx
                break
            k += 1

        if revert_found:
            event_type = "promotion"
            end_date = dates[promo_end_idx]
            confidence = (
                "Price deviated by >= {pct:.1f}% for >= {days} days and reverted "
                "near prior level within {window} days."
            ).format(
                pct=abs((new_level - current_level) / current_level) * 100,
                days=consecutive,
                window=revert_window_days,
            )
        else:
            event_type = "permanent_change"
            # treat the new regime as persisting through the rest of the series
            end_date = dates[n - 1]
            confidence = (
                "Price deviated by >= {pct:.1f}% for >= {days} days and did not "
                "revert to prior level within {window} days."
            ).format(
                pct=abs((new_level - current_level) / current_level) * 100,
                days=consecutive,
                window=revert_window_days,
            )

        pct_change = (new_level - current_level) / current_level if current_level else 0.0

        events.append(
            PriceChangeEvent(
                product_name=product_name,
                start_date=pd.Timestamp(start_date).normalize(),
                end_date=pd.Timestamp(end_date).normalize(),
                old_price=float(round(current_level, 4)),
                new_price=float(round(new_level, 4)),
                pct_change=float(round(pct_change, 4)),
                event_type=event_type,
                confidence_notes=confidence,
            )
        )

        # Move to the new stable regime
        current_level = new_level
        # Continue scanning from j (end of initial persistence block)
        i = j

    return events


def detect_price_change_events(
    df: pd.DataFrame,
    min_rel_change: float = 0.08,
    min_persist_days: int = 3,
    revert_window_days: int = 14,
    revert_tolerance: float = 0.03,
) -> pd.DataFrame:
    """Run price change detection for all products in the dataset.

    Parameters
    ----------
    df : DataFrame
        Raw line-item data as described in the module docstring.
    min_rel_change : float
        Minimum relative change (e.g., 0.08 for 8%%) to consider a change.
    min_persist_days : int
        Minimum consecutive selling days for a candidate regime.
    revert_window_days : int
        Window to look for price reversion and classify as promotion.
    revert_tolerance : float
        Relative tolerance around the old level to call it a reversion.

    Returns
    -------
    DataFrame
        Columns: product_name, start_date, end_date, old_price, new_price,
        pct_change, event_type, confidence_notes.
    """

    daily = _prepare_daily_price(df)

    all_events: List[PriceChangeEvent] = []

    for product_name, pdf in daily.groupby("product_name"):
        events = _detect_events_for_product(
            pdf,
            product_name=product_name,
            min_rel_change=min_rel_change,
            min_persist_days=min_persist_days,
            revert_window_days=revert_window_days,
            revert_tolerance=revert_tolerance,
        )
        all_events.extend(events)

    if not all_events:
        # Return an empty DataFrame with the expected columns.
        return pd.DataFrame(
            columns=[
                "product_name",
                "start_date",
                "end_date",
                "old_price",
                "new_price",
                "pct_change",
                "event_type",
                "confidence_notes",
            ]
        )

    result = pd.DataFrame([
        {
            "product_name": e.product_name,
            "start_date": e.start_date,
            "end_date": e.end_date,
            "old_price": e.old_price,
            "new_price": e.new_price,
            "pct_change": e.pct_change,
            "event_type": e.event_type,
            "confidence_notes": e.confidence_notes,
        }
        for e in all_events
    ])

    # Sort for readability
    result = result.sort_values(["product_name", "start_date"]).reset_index(drop=True)
    return result


__all__ = ["detect_price_change_events", "PriceChangeEvent"]
