# Receipt-Driven Price Elasticity & Promo ROI Analyzer

A small, end-to-end project that uses synthetic grocery receipts to:
- detect price changes and promotions,
- estimate product-level price elasticity, and
- simulate the revenue/ROI impact of different discount depths.

The goal is to demonstrate a clear, defensible workflow that a pricing or
analytics team could adapt for real retail data.

----

## Quickstart

From a clean clone:

```bash
# (optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# install minimal dependencies
pip install -r requirements.txt

# run the full synthetic pipeline (price changes → elasticity → promo ROI)
python src/run_all.py
```

Key outputs will be written to `reports/tables/`.

---

## Overview & Business Problem

Retailers run constant discounts and promotions but often cannot answer:
- *How sensitive is demand to price?*
- *Which discounts drive profitable incremental sales vs. destroy margin?*

This project builds a **receipt-driven pipeline** that turns line-item
transaction data into:
1. Detected price-change / promotion events.
2. Baseline **own-price elasticity** per SKU.
3. Forward-looking **promo ROI scenarios** for different discount levels.

---

## Data

### Synthetic sample data

For this portfolio version, all analysis is based on a synthetic dataset:

- `data/sample/synthetic_receipts.csv`
  - 500+ line-items of grocery receipts
  - Columns: `transaction_id, timestamp, product_name, category, quantity, unit_price, line_total`
  - 30–60 days of activity across 20+ products
  - Includes:
    - 2 temporary promotions (short-lived price drops)
    - 1 permanent price increase for a staple product
  - `line_total` is constructed to equal `quantity * unit_price`.

This file is **tracked in git** so the project is fully reproducible.

### Real data policy

If you plug in actual retailer receipts, those must live under:

- `data/raw/` – **never committed** (gitignored)

The rest of the pipeline (features, models, reports) is designed so that
only **aggregated artifacts** and **synthetic examples** are versioned.

For messy real-world product strings, you can optionally provide a
canonical mapping:

- `data/sample/product_name_map.csv`
  - Columns: `raw_name, canonical_name, category`
  - When present, the runner scripts will map raw product names onto a
    cleaner `canonical_name` and (optionally) overwrite / fill the
    `category` field before any modeling.

---

## Methods

### 1. Price-change & promo detection

Module: `src/features/price_change_detection.py`

1. Aggregate receipts to **daily median unit_price** and **daily quantity** per product.
2. Smooth prices with a **7-day rolling median** per product.
3. Detect change points where the smoothed price moves by **≥ 8%** relative
   to the prior stable level and persists for **≥ 3 consecutive selling days**.
4. Classify each event as:
   - `promotion` if price reverts near the old level within **14 days**.
   - `permanent_change` otherwise.

Output (via `src/run_price_change_detection.py`):
- `reports/tables/price_change_events.csv` with
  `product_name, start_date, end_date, old_price, new_price, pct_change, event_type, confidence_notes`.

### 2. Price elasticity estimation

Module: `src/features/elasticity_model.py`

1. Aggregate to **daily level per product**:
   - `daily_qty` = sum of `quantity`
   - `daily_price` = median `unit_price`.
2. Create `log_qty` and `log_price` (drop nonpositive observations).
3. Add **day-of-week (DOW) categorical controls**.
4. For each product with sufficient data (currently conservative
   thresholds), fit a log–log OLS model using `statsmodels`:

   ```python path=null start=null
   log_qty = β0 + β1 * log_price + DOW dummies + ε
   ```

5. Interpret **β₁** as own-price elasticity (typically negative).

Output (via `src/run_elasticity.py`):
- `reports/tables/elasticity_estimates.csv` with
  `product_name, elasticity, ci_low, ci_high, p_value, n_days, unique_prices, r2`.

> Note: On the current synthetic data and conservative thresholds, this file
> may contain only headers (no products meeting the minimum data criteria).

### 3. Promo ROI simulation

Module: `src/features/promo_roi.py`

Inputs per product:
- `baseline_price` (recent median daily price),
- `baseline_daily_qty` (recent average daily quantity),
- `elasticity`,
- optional `unit_cost`.

For each discount level **5%, 10%, 15%, 20%**:

```python path=null start=null
new_price = baseline_price * (1 - discount)
expected_qty = baseline_daily_qty * (new_price / baseline_price) ** elasticity
expected_revenue = new_price * expected_qty
baseline_revenue = baseline_price * baseline_daily_qty
revenue_change = expected_revenue - baseline_revenue
```

If `unit_cost` is provided, the script also computes baseline and expected
**gross profit** and `profit_change`.

`src/run_promo_simulation.py` wires everything together:
- Computes 14‑day baselines from receipts.
- Joins with elasticity estimates.
- Runs scenarios for the top products by revenue.

Output:
- `reports/tables/promo_scenarios.csv` with one row per
  `(product_name, discount_pct)`.

---

## Results Artifacts

The pipeline writes structured outputs under `reports/`:

- **Price-change events**
  - `reports/tables/price_change_events.csv`
- **Elasticity estimates**
  - `reports/tables/elasticity_estimates.csv`
- **Promo ROI scenarios**
  - `reports/tables/promo_scenarios.csv`

If present, the following figures can be referenced in the README or a
slide deck:

- `reports/figures/example_price_change.png` – price series with detected
  change points highlighted.
- `reports/figures/elasticity_summary.png` – horizontal bar chart of
  elasticity estimates with confidence intervals.
- `reports/figures/promo_price_median.png` / `promo_roi_curves.png` –
  discount vs. revenue/profit change curves for key products.

(The exact set of figures depends on which optional plotting scripts you
choose to run.)

---

## How to Run

From the project root, with dependencies installed:

```bash
# 1) Detect price changes and promotions
python src/run_price_change_detection.py

# 2) Estimate price elasticity per product (where data allows)
python src/run_elasticity.py

# 3) Simulate promo ROI scenarios using elasticity + recent baselines
python src/run_promo_simulation.py
```

Synthetic receipts in `data/sample/` are already included, so you can run
these commands immediately after installing the requirements.

To explore the data interactively:

```bash
# Launch Jupyter and open the EDA notebook
jupyter notebook notebooks/01_eda.ipynb
```

---

## Limitations

- **Synthetic data**: All examples use synthetic receipts; real-world
  noise, assortment complexity, and promotion mechanics are richer.
- **Single-SKU elasticity**: The baseline model is *own-price only*; it
  does not yet model cross-product substitution or category effects.
- **Conservative filters**: The elasticity step currently requires quite
  a bit of data per product; small samples are skipped rather than
  overfit.
- **No promotion costs/COGS**: The promo ROI simulation assumes unit
  cost is either unknown or provided separately; in this repo it is left
  as `NaN`.
- **No causal guarantees**: The regression is descriptive, not
  fully causal; promotion and price decisions may still be endogenous.

---

## Next Steps

If you wanted to extend this into a production-grade analytics asset:

- Relax or hierarchically pool elasticity estimates to cover more SKUs.
- Add COGS and promo cost inputs to move from revenue to **true ROI**.
- Incorporate panel or hierarchical models to borrow strength across
  similar products.
- Add cross-elasticity estimation and basket-level metrics (attach
  co-purchased items from the same transaction).
- Wrap the pipeline in a lightweight API or dashboard for business users.

---

## Project Structure

```text
receipt-price-elasticity-promo-roi/
├── src/
│   ├── features/
│   │   ├── elasticity_model.py
│   │   ├── price_change_detection.py
│   │   └── promo_roi.py
│   ├── run_elasticity.py
│   ├── run_price_change_detection.py
│   └── run_promo_simulation.py
├── notebooks/
│   └── 01_eda.ipynb
├── data/
│   ├── raw/        # real receipts here (never committed)
│   └── sample/     # synthetic receipts used in this repo
├── reports/
│   ├── figures/
│   └── tables/
├── requirements.txt
└── README.md
```

---

## Getting Started

```bash
# 1. Create and activate a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the end-to-end pipeline on synthetic data
python src/run_price_change_detection.py
python src/run_elasticity.py
python src/run_promo_simulation.py
```

You can then inspect CSV outputs under `reports/tables/` and any
generated figures under `reports/figures/`.
