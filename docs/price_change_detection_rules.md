# Price Change & Promotion Detection Rules

This document defines algorithmic rules for detecting price changes and distinguishing temporary promotions from permanent price updates using receipt data only.

---

## Table of Contents

1. [Overview](#overview)
2. [Data Requirements](#data-requirements)
3. [Detection Methodology](#detection-methodology)
4. [Price Change Detection](#price-change-detection)
5. [Promotion Detection](#promotion-detection)
6. [Distinguishing Temporary vs. Permanent Changes](#distinguishing-temporary-vs-permanent-changes)
7. [Validation Logic](#validation-logic)
8. [Edge Cases & Troubleshooting](#edge-cases--troubleshooting)
9. [Implementation Example](#implementation-example)

---

## Overview

### Challenge
Receipt data often lacks explicit promotion flags or may have incomplete/inaccurate flags. We need algorithmic methods to:
1. Detect when a product's price has changed
2. Classify changes as temporary promotions vs. permanent price adjustments
3. Handle noisy data (outliers, data entry errors, regional variations)

### Approach
Use **rolling statistics** and **threshold-based rules** to infer price behavior from transaction patterns.

---

## Data Requirements

### Minimum Fields Required
- `transaction_date`: Date of transaction
- `upc` or `product_id`: Product identifier
- `final_price`: Price paid by customer (post-discount)
- `quantity`: Units purchased (for validation)
- `store_id` (optional but recommended): To handle regional pricing

### Helpful but Optional
- `regular_price`: Manufacturer's suggested retail price
- `discount_amount`: Explicit discount applied
- `is_promotion`: Existing promotion flag (to validate our detection)

### Aggregation Level
Analysis should be performed at:
- **Product-Day** level (for daily price monitoring), or
- **Product-Week** level (for weekly analysis, more stable)

---

## Detection Methodology

### Step 1: Calculate Baseline Price
For each product, establish a "normal" or "baseline" price using a rolling window.

**Rolling Baseline Price (30-day window)**:
```python
baseline_price = df.groupby('upc')['final_price'].rolling(
    window=30, 
    min_periods=10
).median().shift(1)  # Shift to avoid look-ahead bias
```

**Why median?**
- Robust to outliers (discount days won't skew baseline)
- Represents typical non-promotional price

**Alternative: Mode Price**
```python
# Most frequent price in last 30 days (works well for stable pricing)
baseline_price = df.groupby('upc')['final_price'].rolling(
    window=30
).apply(lambda x: x.mode()[0] if len(x.mode()) > 0 else x.median())
```

### Step 2: Calculate Price Deviation
Compare current price to baseline:
```python
price_deviation_pct = (final_price - baseline_price) / baseline_price * 100
```

### Step 3: Apply Thresholds
Define thresholds to classify price behavior.

---

## Price Change Detection

### Rule 1: Significant Price Drop (Potential Promotion)
**Threshold**: Price drops by ≥ 10% from baseline

**Logic**:
```python
is_price_drop = (price_deviation_pct <= -10.0)
```

**Interpretation**:
- Likely a temporary promotion (discount, sale, coupon)
- Requires further analysis to confirm duration

### Rule 2: Significant Price Increase
**Threshold**: Price increases by ≥ 5% from baseline

**Logic**:
```python
is_price_increase = (price_deviation_pct >= 5.0)
```

**Interpretation**:
- Could be permanent price increase (inflation, cost changes)
- Could be correction after prolonged promotion period
- Requires duration analysis to distinguish

### Rule 3: Stable Pricing (No Change)
**Threshold**: Price within ±5% of baseline

**Logic**:
```python
is_stable = (abs(price_deviation_pct) < 5.0)
```

**Interpretation**:
- Business as usual, no promotional or permanent changes

### Threshold Summary Table

| Condition | Threshold | Classification |
|-----------|-----------|----------------|
| `price_deviation_pct <= -20%` | Deep discount | Likely strong promotion |
| `-20% < price_deviation_pct <= -10%` | Moderate discount | Likely promotion |
| `-10% < price_deviation_pct < -5%` | Minor discount | Small promotion or pricing noise |
| `-5% <= price_deviation_pct <= 5%` | Stable | No change |
| `5% < price_deviation_pct < 10%` | Minor increase | Potential permanent increase |
| `price_deviation_pct >= 10%` | Major increase | Likely permanent increase or correction |

---

## Promotion Detection

### Method 1: Rolling Window + Threshold
**Definition**: A promotion is a temporary price drop that reverts to baseline within N days.

**Algorithm**:
1. Detect price drop (≥ 10% below baseline)
2. Check if price returns to baseline within 7-14 days
3. If yes → classify as **promotion**
4. If no → investigate further (could be permanent price reduction)

**Implementation**:
```python
def detect_promotion(df, product_upc, lookback_days=30, promo_threshold=-10.0, revert_days=14):
    """
    Detect promotions for a given product.
    
    Args:
        df: DataFrame with transaction data
        product_upc: Product identifier
        lookback_days: Days to calculate baseline (default 30)
        promo_threshold: % deviation to flag promotion (default -10%)
        revert_days: Days to check for price reversion (default 14)
    
    Returns:
        DataFrame with promotion flags
    """
    # Filter to product
    pdf = df[df['upc'] == product_upc].copy()
    pdf = pdf.sort_values('transaction_date')
    
    # Calculate rolling baseline (median of last 30 days)
    pdf['baseline_price'] = pdf['final_price'].rolling(
        window=lookback_days, min_periods=10
    ).median().shift(1)
    
    # Calculate deviation
    pdf['price_deviation_pct'] = (
        (pdf['final_price'] - pdf['baseline_price']) / pdf['baseline_price'] * 100
    )
    
    # Flag potential promotions (price drops)
    pdf['potential_promo'] = pdf['price_deviation_pct'] <= promo_threshold
    
    # Check for reversion to baseline within revert_days
    pdf['is_promotion'] = False
    for idx in pdf[pdf['potential_promo']].index:
        future_prices = pdf.loc[
            (pdf.index > idx) & 
            (pdf['transaction_date'] <= pdf.loc[idx, 'transaction_date'] + pd.Timedelta(days=revert_days))
        ]['price_deviation_pct']
        
        # If price returns to within 5% of baseline, confirm promotion
        if len(future_prices) > 0 and any(abs(future_prices) < 5.0):
            pdf.loc[idx, 'is_promotion'] = True
    
    return pdf
```

### Method 2: Frequency-Based Detection
**Definition**: Prices that occur rarely (< 20% of observations) are likely promotional.

**Algorithm**:
```python
# Calculate price frequency for each product
price_freq = df.groupby(['upc', 'final_price']).size() / df.groupby('upc').size()

# Flag prices that occur less than 20% of the time
df['is_rare_price'] = df.apply(
    lambda row: price_freq.loc[(row['upc'], row['final_price'])] < 0.20,
    axis=1
)

# Combine with price drop rule
df['is_promotion'] = df['is_rare_price'] & (df['price_deviation_pct'] <= -10.0)
```

### Method 3: Volume Spike Detection
**Definition**: Promotions often drive increased purchase volume.

**Algorithm**:
```python
# Calculate baseline quantity (rolling 30-day average)
df['baseline_quantity'] = df.groupby('upc')['quantity'].rolling(
    window=30, min_periods=10
).mean().shift(1)

# Detect volume spike (>30% increase)
df['volume_spike'] = (df['quantity'] / df['baseline_quantity']) > 1.30

# Promotions = price drop + volume spike
df['is_promotion'] = (df['price_deviation_pct'] <= -10.0) & df['volume_spike']
```

### Combined Promotion Score
**Confidence-based approach**: Assign points for multiple signals.

```python
promotion_score = 0

# +2 points: Significant price drop
if price_deviation_pct <= -10.0:
    promotion_score += 2

# +1 point: Rare price
if is_rare_price:
    promotion_score += 1

# +1 point: Volume spike
if volume_spike:
    promotion_score += 1

# +1 point: Price reverts to baseline
if price_reverts_within_14_days:
    promotion_score += 1

# Classification
if promotion_score >= 3:
    classification = "High Confidence Promotion"
elif promotion_score == 2:
    classification = "Likely Promotion"
else:
    classification = "Uncertain / Not Promotion"
```

---

## Distinguishing Temporary vs. Permanent Changes

### Key Question
Did the price return to its previous level, or is the new price the "new normal"?

### Rule 1: Duration-Based Classification
**Temporary Promotion**:
- Price drop lasts ≤ 14 days
- Price returns to within 5% of baseline after promotion ends

**Permanent Price Reduction**:
- Price drop persists for > 30 days
- No reversion to old baseline

**Implementation**:
```python
def classify_price_change(df, product_upc, duration_threshold=30):
    """
    Classify price changes as temporary or permanent.
    """
    pdf = df[df['upc'] == product_upc].sort_values('transaction_date')
    
    # Identify price drops
    price_drops = pdf[pdf['price_deviation_pct'] <= -10.0]
    
    for idx in price_drops.index:
        drop_date = pdf.loc[idx, 'transaction_date']
        drop_price = pdf.loc[idx, 'final_price']
        baseline = pdf.loc[idx, 'baseline_price']
        
        # Look ahead to see if price persists
        future_data = pdf[pdf['transaction_date'] > drop_date]
        
        # Check if price returns to baseline within 30 days
        revert_window = future_data[
            future_data['transaction_date'] <= drop_date + pd.Timedelta(days=duration_threshold)
        ]
        
        if len(revert_window) > 0:
            avg_future_price = revert_window['final_price'].mean()
            
            # If future price is close to drop price, it's permanent
            if abs(avg_future_price - drop_price) / drop_price < 0.05:
                pdf.loc[idx, 'change_type'] = 'Permanent Price Reduction'
            # If future price returns to baseline, it's temporary
            elif abs(avg_future_price - baseline) / baseline < 0.05:
                pdf.loc[idx, 'change_type'] = 'Temporary Promotion'
            else:
                pdf.loc[idx, 'change_type'] = 'Uncertain'
    
    return pdf
```

### Rule 2: Post-Change Baseline Shift
**Logic**: After a potential permanent change, recalculate baseline and check stability.

```python
# Calculate baseline before and after potential change point
baseline_before = df[df['transaction_date'] < change_date]['final_price'].median()
baseline_after = df[df['transaction_date'] >= change_date]['final_price'].median()

# If baselines differ significantly, it's permanent
if abs(baseline_after - baseline_before) / baseline_before > 0.10:
    change_type = 'Permanent'
else:
    change_type = 'Temporary'
```

### Rule 3: External Validation (if available)
If `regular_price` or `discount_amount` fields are available:

```python
# If discount_amount > 0, it's a promotion
if discount_amount > 0:
    change_type = 'Temporary Promotion'

# If regular_price has changed, it's permanent
if regular_price_current != regular_price_previous:
    change_type = 'Permanent Price Change'
```

---

## Validation Logic

### Validation Check 1: Outlier Detection
**Problem**: Data entry errors can be mistaken for price changes.

**Solution**: Flag extreme deviations for manual review.

```python
# Flag prices more than 3 standard deviations from mean
z_score = (final_price - mean_price) / std_price
is_outlier = abs(z_score) > 3

# Exclude outliers from promotion detection
df_clean = df[~is_outlier]
```

### Validation Check 2: Cross-Store Consistency
**Problem**: Price changes should be consistent across stores (unless regional pricing).

**Solution**: Check if price change occurs in multiple stores.

```python
# For a given product-date, count stores with price drop
stores_with_drop = df.groupby(['upc', 'transaction_date']).agg({
    'store_id': 'nunique',
    'price_deviation_pct': lambda x: (x <= -10.0).sum()
})

# If >50% of stores have price drop, it's a real promotion
is_valid_promo = (stores_with_drop['price_deviation_pct'] / stores_with_drop['store_id']) > 0.50
```

### Validation Check 3: Historical Pattern Matching
**Problem**: Promotions often repeat (e.g., every Black Friday).

**Solution**: Check if similar price drops occurred at the same time in prior years.

```python
# Check if promotion occurred in same week last year
same_week_last_year = df[
    (df['upc'] == product_upc) & 
    (df['week_of_year'] == current_week) &
    (df['year'] == current_year - 1)
]['price_deviation_pct'].mean()

if same_week_last_year <= -10.0:
    confidence = 'High (Recurring Promotion)'
```

### Validation Check 4: Quantity-Price Correlation
**Problem**: Promotions should drive higher purchase volumes.

**Solution**: Check if price drops correlate with quantity increases.

```python
# Calculate correlation between price deviation and quantity
correlation = df.groupby('upc').apply(
    lambda x: x['price_deviation_pct'].corr(x['quantity'])
)

# Negative correlation (-0.3 to -1.0) supports promotion hypothesis
if correlation < -0.30:
    validation_status = 'Valid Promotion Pattern'
```

---

## Edge Cases & Troubleshooting

### Edge Case 1: New Products
**Problem**: No baseline exists for new products.

**Solution**: 
- Require minimum 30 days of data before detecting promotions
- Use category-level baseline as proxy

### Edge Case 2: Highly Volatile Pricing
**Problem**: Products with frequent small price changes (e.g., fresh produce).

**Solution**:
- Increase threshold to ≥ 20% for volatile categories
- Use longer rolling windows (60-90 days)

### Edge Case 3: Clearance Sales
**Problem**: Permanent markdowns may be mistaken for promotions.

**Solution**:
- Check for sustained low prices (> 60 days) → reclassify as clearance
- Flag products with declining sales volume (indicator of discontinuation)

### Edge Case 4: Regional Pricing
**Problem**: Different stores may have different baseline prices.

**Solution**:
- Calculate baseline at store-product level, not just product level
- Use store-specific thresholds

### Edge Case 5: Bundle Pricing
**Problem**: "Buy 2 Get 1 Free" may not show price drop per unit.

**Solution**:
- Calculate effective price: `final_price / quantity`
- Detect promotions based on effective price deviation

---

## Implementation Example

### Full Pipeline

```python
import pandas as pd
import numpy as np

def detect_price_changes_and_promotions(df, 
                                        lookback_days=30,
                                        promo_threshold=-10.0,
                                        revert_days=14,
                                        min_observations=10):
    """
    Full pipeline for detecting price changes and promotions.
    
    Args:
        df: DataFrame with columns [transaction_date, upc, final_price, quantity, store_id]
        lookback_days: Rolling window for baseline calculation
        promo_threshold: % deviation threshold for promotion detection
        revert_days: Days to check for price reversion
        min_observations: Minimum observations required to calculate baseline
    
    Returns:
        DataFrame with added columns: 
            - baseline_price
            - price_deviation_pct
            - is_promotion
            - change_type
            - confidence_score
    """
    
    # Sort by product and date
    df = df.sort_values(['upc', 'transaction_date']).reset_index(drop=True)
    
    # Step 1: Calculate baseline price (rolling median)
    df['baseline_price'] = df.groupby('upc')['final_price'].transform(
        lambda x: x.rolling(window=lookback_days, min_periods=min_observations).median().shift(1)
    )
    
    # Step 2: Calculate price deviation
    df['price_deviation_pct'] = (
        (df['final_price'] - df['baseline_price']) / df['baseline_price'] * 100
    )
    
    # Step 3: Calculate baseline quantity
    df['baseline_quantity'] = df.groupby('upc')['quantity'].transform(
        lambda x: x.rolling(window=lookback_days, min_periods=min_observations).mean().shift(1)
    )
    
    # Step 4: Detect volume spike
    df['volume_spike'] = (df['quantity'] / df['baseline_quantity']) > 1.30
    
    # Step 5: Detect rare prices
    price_freq = df.groupby(['upc', 'final_price']).size() / df.groupby('upc').size()
    df['is_rare_price'] = df.apply(
        lambda row: price_freq.get((row['upc'], row['final_price']), 1.0) < 0.20,
        axis=1
    )
    
    # Step 6: Calculate confidence score
    df['confidence_score'] = 0
    df.loc[df['price_deviation_pct'] <= promo_threshold, 'confidence_score'] += 2
    df.loc[df['is_rare_price'], 'confidence_score'] += 1
    df.loc[df['volume_spike'], 'confidence_score'] += 1
    
    # Step 7: Classify as promotion
    df['is_promotion'] = df['confidence_score'] >= 3
    
    # Step 8: Distinguish temporary vs. permanent (simplified)
    df['change_type'] = 'Stable'
    df.loc[df['is_promotion'], 'change_type'] = 'Temporary Promotion'
    df.loc[
        (df['price_deviation_pct'] <= promo_threshold) & (~df['is_promotion']),
        'change_type'
    ] = 'Potential Permanent Reduction'
    df.loc[df['price_deviation_pct'] >= 5.0, 'change_type'] = 'Price Increase'
    
    return df


# Example usage
receipts = pd.read_csv('data/processed/receipts_clean.csv', parse_dates=['transaction_date'])
receipts_with_flags = detect_price_changes_and_promotions(receipts)

# Summary
print(receipts_with_flags['change_type'].value_counts())
print(receipts_with_flags['is_promotion'].value_counts())
```

---

## Summary Decision Tree

```
Is price_deviation <= -10%?
│
├─ YES → Is this a rare price (< 20% frequency)?
│        │
│        ├─ YES → Is there a volume spike (>30%)?
│        │        │
│        │        ├─ YES → HIGH CONFIDENCE PROMOTION
│        │        └─ NO  → LIKELY PROMOTION
│        │
│        └─ NO  → Does price revert within 14 days?
│                 │
│                 ├─ YES → TEMPORARY PROMOTION
│                 └─ NO  → POTENTIAL PERMANENT REDUCTION
│
└─ NO  → Is price_deviation >= 5%?
         │
         ├─ YES → Does price persist > 30 days?
         │        │
         │        ├─ YES → PERMANENT PRICE INCREASE
         │        └─ NO  → TEMPORARY INCREASE (rare)
         │
         └─ NO  → STABLE PRICING (no change)
```

---

## Output Schema

After running detection pipeline, the output should include:

| Column | Description |
|--------|-------------|
| `baseline_price` | Rolling median price (30-day window) |
| `price_deviation_pct` | % deviation from baseline |
| `is_promotion` | Boolean flag for detected promotion |
| `change_type` | Classification: Stable, Temporary Promotion, Permanent Reduction, Price Increase |
| `confidence_score` | 0-4 score based on multiple signals |
| `volume_spike` | Boolean flag for quantity increase |
| `is_rare_price` | Boolean flag for infrequent prices |

---

**Document Version**: 1.0  
**Last Updated**: 2023-12-21  
**Author**: Analytics Team
