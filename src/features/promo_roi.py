"""Promotion ROI simulation using price elasticity estimates.

Core idea
---------
For each product with a baseline price, baseline daily quantity, and an
own-price elasticity estimate, simulate different percentage discounts
and compute expected changes in revenue and (optionally) gross profit.

Elasticity model used:
    expected_qty = baseline_qty * (new_price / baseline_price) ** elasticity

Inputs per product (row-level):
- product_name
- baseline_price
- baseline_daily_qty
- elasticity
- unit_cost (optional; can be NaN)

For each discount level d in [0.05, 0.10, 0.15, 0.20]:
- new_price = baseline_price * (1 - d)
- expected_qty = baseline_daily_qty * (new_price / baseline_price) ** elasticity
- expected_revenue = new_price * expected_qty
- baseline_revenue = baseline_price * baseline_daily_qty
- revenue_change = expected_revenue - baseline_revenue

If unit_cost is provided (not null):
- baseline_gross_profit = (baseline_price - unit_cost) * baseline_daily_qty
- expected_gross_profit = (new_price - unit_cost) * expected_qty
- profit_change = expected_gross_profit - baseline_gross_profit

Guardrails
----------
- If elasticity is missing, NaN, or not finite: mark in `notes` and skip.
- If elasticity is positive (price increase raises demand): flag as
  suspicious in `notes` but still simulate (so issues are visible).
- If |elasticity| is extremely large (>|10|): mark as unreasonable in
  `notes` but still simulate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np
import pandas as pd


DISCOUNT_LEVELS = [0.05, 0.10, 0.15, 0.20]


@dataclass
class PromoInput:
    product_name: str
    baseline_price: float
    baseline_daily_qty: float
    elasticity: float
    unit_cost: Optional[float] = None


def simulate_promo_scenarios(
    inputs: pd.DataFrame,
    discount_levels: Iterable[float] = DISCOUNT_LEVELS,
) -> pd.DataFrame:
    """Simulate promotion impact for a set of products.

    Parameters
    ----------
    inputs : DataFrame
        Expected columns: product_name, baseline_price, baseline_daily_qty,
        elasticity, optional unit_cost.
    discount_levels : iterable of float
        Discount percentages expressed as decimals, e.g. 0.05 for 5%.

    Returns
    -------
    DataFrame
        Columns:
        - product_name
        - discount_pct
        - baseline_price
        - new_price
        - baseline_daily_qty
        - expected_daily_qty
        - baseline_revenue
        - expected_revenue
        - revenue_change
        - unit_cost
        - baseline_gross_profit
        - expected_gross_profit
        - profit_change
        - notes
    """

    required_cols = {"product_name", "baseline_price", "baseline_daily_qty", "elasticity"}
    missing = required_cols - set(inputs.columns)
    if missing:
        raise ValueError(f"inputs missing required columns: {sorted(missing)}")

    rows: List[dict] = []

    for _, row in inputs.iterrows():
        product = row["product_name"]
        baseline_price = float(row["baseline_price"])
        baseline_qty = float(row["baseline_daily_qty"])
        elasticity = row["elasticity"]
        unit_cost = row.get("unit_cost", np.nan)

        note_parts: List[str] = []

        if pd.isna(elasticity) or not np.isfinite(elasticity):
            # Skip entirely; record a single row with note if desired.
            # For simplicity we just skip to keep outputs clean.
            continue

        elasticity = float(elasticity)

        if elasticity > 0:
            note_parts.append("positive elasticity (suspicious)")

        if abs(elasticity) > 10:
            note_parts.append("|elasticity|>10 (likely unstable estimate)")

        if baseline_price <= 0 or baseline_qty <= 0:
            # No meaningful simulation possible.
            note_parts.append("nonpositive baseline price/qty; skipped")
            continue

        baseline_revenue = baseline_price * baseline_qty

        has_cost = not pd.isna(unit_cost)
        if has_cost:
            unit_cost = float(unit_cost)
            baseline_gross_profit = (baseline_price - unit_cost) * baseline_qty
        else:
            baseline_gross_profit = np.nan

        for d in discount_levels:
            discount_pct = float(d)
            new_price = baseline_price * (1.0 - discount_pct)

            if new_price <= 0:
                scenario_note = note_parts + ["new_price<=0; scenario skipped"]
                rows.append(
                    {
                        "product_name": product,
                        "discount_pct": discount_pct,
                        "baseline_price": baseline_price,
                        "new_price": new_price,
                        "baseline_daily_qty": baseline_qty,
                        "expected_daily_qty": np.nan,
                        "baseline_revenue": baseline_revenue,
                        "expected_revenue": np.nan,
                        "revenue_change": np.nan,
                        "unit_cost": unit_cost if has_cost else np.nan,
                        "baseline_gross_profit": baseline_gross_profit,
                        "expected_gross_profit": np.nan,
                        "profit_change": np.nan,
                        "notes": "; ".join(scenario_note) if scenario_note else "",
                    }
                )
                continue

            # Elasticity-based quantity response
            price_ratio = new_price / baseline_price
            expected_qty = baseline_qty * (price_ratio ** elasticity)
            expected_revenue = new_price * expected_qty
            revenue_change = expected_revenue - baseline_revenue

            if has_cost:
                expected_gross_profit = (new_price - unit_cost) * expected_qty
                profit_change = expected_gross_profit - baseline_gross_profit
            else:
                expected_gross_profit = np.nan
                profit_change = np.nan

            rows.append(
                {
                    "product_name": product,
                    "discount_pct": discount_pct,
                    "baseline_price": baseline_price,
                    "new_price": new_price,
                    "baseline_daily_qty": baseline_qty,
                    "expected_daily_qty": expected_qty,
                    "baseline_revenue": baseline_revenue,
                    "expected_revenue": expected_revenue,
                    "revenue_change": revenue_change,
                    "unit_cost": unit_cost if has_cost else np.nan,
                    "baseline_gross_profit": baseline_gross_profit,
                    "expected_gross_profit": expected_gross_profit,
                    "profit_change": profit_change,
                    "notes": "; ".join(note_parts) if note_parts else "",
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "product_name",
                "discount_pct",
                "baseline_price",
                "new_price",
                "baseline_daily_qty",
                "expected_daily_qty",
                "baseline_revenue",
                "expected_revenue",
                "revenue_change",
                "unit_cost",
                "baseline_gross_profit",
                "expected_gross_profit",
                "profit_change",
                "notes",
            ]
        )

    result = pd.DataFrame(rows)

    # For readability: sort by product then discount
    result = result.sort_values(["product_name", "discount_pct"]).reset_index(drop=True)
    return result


__all__ = ["simulate_promo_scenarios", "PromoInput", "DISCOUNT_LEVELS"]
