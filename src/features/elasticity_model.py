import numpy as np, pandas as pd
from scipy import stats

# log-log ols per product: log_qty ~ log_price + dow dummies
# plain numpy lstsq so it's fast + no statsmodels dep

MIN_DAYS = 14
MIN_UNIQUE_PRICES = 3


def _fit(y, X):
    beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    n, k = X.shape
    dof = n - k
    sigma2 = resid @ resid / dof
    xtx_inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(sigma2 * xtx_inv))
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid @ resid) / ss_tot if ss_tot > 0 else np.nan
    return beta, se, dof, r2


def estimate_product(sub):
    sub = sub[(sub.daily_qty > 0) & (sub.daily_price > 0)].copy()
    if len(sub) < MIN_DAYS or sub.daily_price.nunique() < MIN_UNIQUE_PRICES:
        return None

    sub["log_qty"] = np.log(sub.daily_qty)
    sub["log_price"] = np.log(sub.daily_price)
    dow = pd.get_dummies(pd.to_datetime(sub.date).dt.dayofweek, prefix="dow", drop_first=True).astype(float)

    X = np.column_stack([np.ones(len(sub)), sub.log_price.to_numpy(), dow.to_numpy()])
    y = sub.log_qty.to_numpy()
    if X.shape[0] <= X.shape[1]:
        return None

    beta, se, dof, r2 = _fit(y, X)
    b, s = beta[1], se[1]
    t = b / s if s else np.nan
    p = 2 * stats.t.sf(abs(t), dof)
    crit = stats.t.ppf(0.975, dof)
    return {
        "elasticity": round(float(b), 4),
        "ci_low": round(float(b - crit * s), 4),
        "ci_high": round(float(b + crit * s), 4),
        "p_value": round(float(p), 4),
        "n_days": int(len(sub)),
        "unique_prices": int(sub.daily_price.nunique()),
        "r2": round(float(r2), 4),
    }


def estimate(daily):
    rows = []
    for name, sub in daily.groupby("product_name", sort=False):
        r = estimate_product(sub)
        if r:
            rows.append({"product_name": name, **r})
    return pd.DataFrame(rows, columns=[
        "product_name","elasticity","ci_low","ci_high","p_value",
        "n_days","unique_prices","r2"])
