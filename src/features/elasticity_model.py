"""Estimate own-price elasticity per product from receipt line-item data.

This module implements a standard log-log demand model with day-of-week
controls, estimated separately for each product.

Model (per product):

    log(qty_t) = beta_0 + beta_1 * log(price_t) + DOW controls + error_t

where beta_1 is interpreted as own-price elasticity (typically negative).

Requirements implemented here:
- Input: DataFrame with columns [timestamp, product_name, quantity, unit_price].
- Aggregate to daily level per product: daily_qty (sum quantity) and
  daily_price (median unit_price).
- Create log_qty and log_price (dropping nonpositive values safely).
- Add day-of-week as categorical controls.
- Fit statsmodels OLS for each product with at least 20 valid days and
  at least 6 unique price points.
- Output per product: product_name, elasticity (coef on log_price),
  ci_low, ci_high, p_value, n_days, unique_prices, r2.
- Conservatively handle sparse products: skip and record a reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass
class ElasticityResult:
    product_name: str
    elasticity: float
    ci_low: float
    ci_high: float
    p_value: float
    n_days: int
    unique_prices: int
    r2: float


@dataclass
class SkipReason:
    product_name: str
    reason: str
    n_days: int
    unique_prices: int


def _aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate line-items to daily quantity and median price per product.

    Returns columns:
    - product_name
    - date
    - daily_qty
    - daily_price
    - dow (day of week as string)
    """

    required = {"timestamp", "product_name", "quantity", "unit_price"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input DataFrame missing columns: {sorted(missing)}")

    tmp = df.copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"])
    tmp["date"] = tmp["timestamp"].dt.date

    daily = (
        tmp.groupby(["product_name", "date"], as_index=False)
        .agg(
            daily_qty=("quantity", "sum"),
            daily_price=("unit_price", "median"),
        )
        .sort_values(["product_name", "date"])
    )

    daily["date"] = pd.to_datetime(daily["date"])
    daily["dow"] = daily["date"].dt.day_name()
    return daily


def _prepare_design_matrix(pdf: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    """Create y (log_qty) and X (log_price + DOW dummies) for one product.

    Drops rows with nonpositive qty/price or missing values.
    """

    dfp = pdf.copy()
    # Guard against zeros / negatives
    dfp = dfp[(dfp["daily_qty"] > 0) & (dfp["daily_price"] > 0)].copy()
    if dfp.empty:
        return pd.Series(dtype=float), pd.DataFrame()

    dfp["log_qty"] = np.log(dfp["daily_qty"])
    dfp["log_price"] = np.log(dfp["daily_price"])

    # Drop any remaining NaNs
    dfp = dfp.dropna(subset=["log_qty", "log_price", "dow"])
    if dfp.empty:
        return pd.Series(dtype=float), pd.DataFrame()

    y = dfp["log_qty"]

    # Day-of-week dummies (drop_first=True for identifiability)
    dow_dummies = pd.get_dummies(dfp["dow"], prefix="dow", drop_first=True)

    X = pd.concat([dfp[["log_price"]], dow_dummies], axis=1)
    X = sm.add_constant(X)
    return y, X


def estimate_elasticity_per_product(
    df: pd.DataFrame,
    min_days: int = 20,
    min_unique_prices: int = 6,
    alpha: float = 0.05,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate own-price elasticity per product.

    Parameters
    ----------
    df : DataFrame
        Line-item data with at least the required columns.
    min_days : int
        Minimum number of valid daily observations required per product.
    min_unique_prices : int
        Minimum number of unique daily prices required per product.
    alpha : float
        Significance level for confidence intervals (default 0.05 → 95% CI).

    Returns
    -------
    (estimates, skipped)
        estimates : DataFrame with columns
            [product_name, elasticity, ci_low, ci_high, p_value,
             n_days, unique_prices, r2]
        skipped : DataFrame with columns
            [product_name, reason, n_days, unique_prices]
    """

    daily = _aggregate_daily(df)

    results: List[ElasticityResult] = []
    skipped: List[SkipReason] = []

    z = 1.96  # approximate for 95% CI; could use t-dist but fine for MVP

    for product_name, pdf in daily.groupby("product_name"):
        n_days = len(pdf)
        unique_prices = pdf["daily_price"].nunique(dropna=True)

        if n_days < min_days:
            skipped.append(
                SkipReason(
                    product_name=product_name,
                    reason=f"insufficient days (<{min_days})",
                    n_days=n_days,
                    unique_prices=unique_prices,
                )
            )
            continue

        if unique_prices < min_unique_prices:
            skipped.append(
                SkipReason(
                    product_name=product_name,
                    reason=f"insufficient unique prices (<{min_unique_prices})",
                    n_days=n_days,
                    unique_prices=unique_prices,
                )
            )
            continue

        y, X = _prepare_design_matrix(pdf)
        if y.empty or X.empty or X.shape[0] < min_days:
            skipped.append(
                SkipReason(
                    product_name=product_name,
                    reason="no valid observations after log/filtering",
                    n_days=int(X.shape[0]) if not X.empty else 0,
                    unique_prices=unique_prices,
                )
            )
            continue

        try:
            model = sm.OLS(y, X).fit()
        except Exception as exc:  # pragma: no cover - defensive
            skipped.append(
                SkipReason(
                    product_name=product_name,
                    reason=f"OLS failed: {exc.__class__.__name__}",
                    n_days=int(X.shape[0]),
                    unique_prices=unique_prices,
                )
            )
            continue

        if "log_price" not in model.params:
            skipped.append(
                SkipReason(
                    product_name=product_name,
                    reason="log_price coefficient not found in model params",
                    n_days=int(X.shape[0]),
                    unique_prices=unique_prices,
                )
            )
            continue

        beta = float(model.params["log_price"])
        se = float(model.bse["log_price"])
        pval = float(model.pvalues["log_price"])
        ci_low = beta - z * se
        ci_high = beta + z * se

        results.append(
            ElasticityResult(
                product_name=product_name,
                elasticity=beta,
                ci_low=ci_low,
                ci_high=ci_high,
                p_value=pval,
                n_days=int(X.shape[0]),
                unique_prices=int(unique_prices),
                r2=float(model.rsquared),
            )
        )

    estimates_df = (
        pd.DataFrame([r.__dict__ for r in results])
        if results
        else pd.DataFrame(
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
    )

    skipped_df = (
        pd.DataFrame([s.__dict__ for s in skipped])
        if skipped
        else pd.DataFrame(columns=["product_name", "reason", "n_days", "unique_prices"])
    )

    # Sort estimates for readability
    if not estimates_df.empty:
        estimates_df = estimates_df.sort_values("elasticity").reset_index(drop=True)

    return estimates_df, skipped_df


__all__ = ["estimate_elasticity_per_product"]
