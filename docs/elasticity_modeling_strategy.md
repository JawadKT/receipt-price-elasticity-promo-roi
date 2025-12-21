# Elasticity Modeling Strategy

This document describes the statistical and econometric approach for estimating price elasticity of demand using receipt-level transaction data.

---

## Table of Contents

1. [Overview](#overview)
2. [Theoretical Foundation](#theoretical-foundation)
3. [Baseline Regression Approach](#baseline-regression-approach)
4. [Control Variables](#control-variables)
5. [Model Specifications](#model-specifications)
6. [Assumptions & Limitations](#assumptions--limitations)
7. [Interpretation Guidelines](#interpretation-guidelines)
8. [Model Selection Criteria](#model-selection-criteria)
9. [Implementation Recommendations](#implementation-recommendations)

---

## Overview

### Definition
**Price elasticity of demand** (ε) measures the percentage change in quantity demanded in response to a 1% change in price:

```
ε = (% Change in Quantity) / (% Change in Price)
```

### Typical Range
- **Highly Elastic**: ε < -1.5 (luxury goods, discretionary items)
- **Elastic**: -1.5 ≤ ε < -1.0 (substitutable products)
- **Unit Elastic**: ε ≈ -1.0 (proportional response)
- **Inelastic**: -1.0 < ε < 0 (necessities, staples)

### Business Implications
- **If |ε| > 1**: Price reduction increases total revenue (elastic demand)
- **If |ε| < 1**: Price increase increases total revenue (inelastic demand)
- **If |ε| = 1**: Revenue unchanged by price changes (unit elastic)

---

## Theoretical Foundation

### Demand Function
The standard demand function relates quantity to price and other factors:

```
Q = f(P, I, Ps, Pc, T, ...)
```

Where:
- **Q**: Quantity demanded
- **P**: Price of the product
- **I**: Consumer income
- **Ps**: Prices of substitute products
- **Pc**: Prices of complementary products
- **T**: Tastes, preferences, seasonality

### Functional Forms

#### 1. Log-Log (Constant Elasticity)
```
log(Q) = β₀ + β₁·log(P) + β₂·X + ε
```
- **Elasticity**: ε = β₁ (constant across all price levels)
- **Interpretation**: 1% increase in price → β₁% change in quantity
- **Assumption**: Elasticity does not vary with price level

#### 2. Linear
```
Q = β₀ + β₁·P + β₂·X + ε
```
- **Elasticity**: ε = β₁ · (P/Q) (varies with price and quantity)
- **Interpretation**: $1 increase in price → β₁ unit change in quantity
- **Assumption**: Constant marginal effect

#### 3. Semi-Log
```
log(Q) = β₀ + β₁·P + β₂·X + ε
```
- **Elasticity**: ε = β₁ · P (varies with price)
- **Interpretation**: $1 increase in price → β₁% change in quantity

### Recommended Form
**Log-Log** is preferred for price elasticity estimation because:
- Elasticity is directly interpretable as β₁
- Handles multiplicative relationships naturally
- Reduces heteroscedasticity
- Aligns with economic theory (constant elasticity is a common assumption)

---

## Baseline Regression Approach

### Model 1: Simple Log-Log Regression
**Specification**:
```
log(Qᵢₜ) = β₀ + β₁·log(Pᵢₜ) + εᵢₜ
```

**Variables**:
- `Qᵢₜ`: Quantity of product `i` sold in period `t`
- `Pᵢₜ`: Price of product `i` in period `t`
- `εᵢₜ`: Error term

**Interpretation**:
- **β₁**: Price elasticity of demand
- **Expected sign**: Negative (higher price → lower quantity)

**Implementation**:
```python
import statsmodels.api as sm
import numpy as np

# Log-transform variables
df['log_quantity'] = np.log(df['quantity'])
df['log_price'] = np.log(df['final_price'])

# Fit model
X = sm.add_constant(df['log_price'])
y = df['log_quantity']
model = sm.OLS(y, X).fit()

# Extract elasticity
elasticity = model.params['log_price']
print(f"Price Elasticity: {elasticity:.3f}")
```

### Model 2: Log-Log with Promotion Control
**Specification**:
```
log(Qᵢₜ) = β₀ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + εᵢₜ
```

**New Variable**:
- `Promoᵢₜ`: Binary indicator (1 = promotion active, 0 = no promotion)

**Interpretation**:
- **β₁**: Price elasticity (controlling for promotions)
- **β₂**: Promotional lift (% increase in sales when promotion is active)
- **β₂ > 0**: Promotions increase sales beyond price effect

**Why control for promotions?**
- Promotions create both price changes AND marketing effects
- Without control, elasticity estimates are biased upward (overestimate sensitivity)
- Separates pure price effect from promotional excitement

---

## Control Variables

### Essential Controls

#### 1. Time Fixed Effects
**Purpose**: Control for time-varying factors affecting all products (seasonality, holidays, economic conditions)

**Specification**:
```
log(Qᵢₜ) = β₀ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + γₜ + εᵢₜ
```

**Implementation**:
```python
# Add week or month fixed effects
df['week'] = df['transaction_date'].dt.isocalendar().week
df = pd.get_dummies(df, columns=['week'], prefix='week')

# Include in regression
X = df[['log_price', 'promo_binary'] + [col for col in df.columns if 'week_' in col]]
```

#### 2. Product Fixed Effects
**Purpose**: Control for unobserved product characteristics (brand, quality, package size)

**Specification** (Panel Model):
```
log(Qᵢₜ) = αᵢ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + εᵢₜ
```
- `αᵢ`: Product-specific intercept

**Implementation**:
```python
from linearmodels.panel import PanelOLS

# Set up panel structure
panel_data = df.set_index(['upc', 'week'])

# Fit fixed effects model
fe_model = PanelOLS.from_formula(
    'log_quantity ~ log_price + promo_binary + EntityEffects',
    data=panel_data
).fit(cov_type='clustered', cluster_entity=True)
```

### Recommended Controls

#### 3. Day-of-Week Effects
**Purpose**: Control for weekly shopping patterns

**Variable**: Binary indicators for each day (Monday, Tuesday, ..., Sunday)

```python
df['day_of_week'] = df['transaction_date'].dt.dayofweek
df = pd.get_dummies(df, columns=['day_of_week'], drop_first=True)
```

#### 4. Holiday Indicators
**Purpose**: Control for abnormal shopping during holidays

**Variable**: Binary indicator for major holidays

```python
holidays = ['2023-11-24', '2023-12-25', '2024-01-01']  # Thanksgiving, Christmas, New Year
df['is_holiday'] = df['transaction_date'].isin(pd.to_datetime(holidays))
```

#### 5. Store Fixed Effects
**Purpose**: Control for store-specific factors (location, size, demographics)

**Variable**: Binary indicators for each store

```python
df = pd.get_dummies(df, columns=['store_id'], prefix='store', drop_first=True)
```

#### 6. Lagged Promotion
**Purpose**: Control for stockpiling behavior (consumers buy extra during promotions)

**Variable**: Indicator for promotion in previous week

```python
df['promo_lag1'] = df.groupby('upc')['promo_binary'].shift(1)
```

### Optional Controls

#### 7. Competitive Pricing
**Purpose**: Account for substitution effects

**Variable**: Average price of competing products in same category

```python
df['competitor_avg_price'] = df.groupby(['category', 'transaction_date'])['final_price'].transform(
    lambda x: x.mean()
)
```

#### 8. Temperature/Weather (if available)
**Purpose**: Control for weather-sensitive products (ice cream, soup, beverages)

**Variable**: Daily temperature or precipitation

```python
df = df.merge(weather_data[['date', 'temperature']], 
               left_on='transaction_date', right_on='date', how='left')
```

---

## Model Specifications

### Specification 1: Baseline (OLS)
**Best for**: Quick analysis, single-product estimation

```
log(Qᵢₜ) = β₀ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + εᵢₜ
```

**Pros**:
- Simple and interpretable
- Fast computation
- No special data structure required

**Cons**:
- Ignores unobserved heterogeneity
- Potential omitted variable bias

### Specification 2: Fixed Effects (Panel Model)
**Best for**: Category-level analysis, controlling for product heterogeneity

```
log(Qᵢₜ) = αᵢ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + γₜ + εᵢₜ
```
- `αᵢ`: Product fixed effects
- `γₜ`: Time fixed effects

**Pros**:
- Controls for unobserved product characteristics
- Reduces omitted variable bias
- More credible causal estimate

**Cons**:
- Requires panel structure (multiple products × multiple time periods)
- Computationally intensive

### Specification 3: Full Model with Controls
**Best for**: High-stakes analysis, publication-quality estimates

```
log(Qᵢₜ) = αᵢ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + β₃·Promo_lagᵢₜ₋₁ 
          + β₄·Weekendₜ + β₅·Holidayₜ + γₜ + εᵢₜ
```

**Pros**:
- Comprehensive control for confounders
- Robust to alternative specifications
- Addresses endogeneity concerns

**Cons**:
- Requires extensive data
- Risk of overfitting with small samples

---

## Assumptions & Limitations

### Key Assumptions

#### 1. No Endogeneity (Exogenous Prices)
**Assumption**: Prices are set independently of unobserved demand shocks

**Violation**: Retailers may discount slow-moving products (reverse causality)

**Test**: 
- Check if price changes are correlated with lagged sales
- Use instrumental variables (IV) if endogeneity suspected

**Mitigation**:
- Use fixed effects to control for product-specific demand trends
- Restrict analysis to chain-wide price changes (not store-specific)

#### 2. No Measurement Error
**Assumption**: Prices and quantities are recorded accurately

**Violation**: Scanner errors, missing transactions, aggregation issues

**Mitigation**:
- Clean outliers and validate data
- Use median prices (robust to errors)

#### 3. Homogeneity of Elasticity
**Assumption**: Elasticity is constant across price range (log-log model)

**Violation**: Elasticity may differ at high vs. low prices

**Test**: 
- Estimate separate models for price quartiles
- Use spline regression for flexible functional form

**Mitigation**:
- Accept as approximation for typical price range
- Report elasticity at mean price

#### 4. Independence of Observations
**Assumption**: Sales in one period do not affect sales in another (no autocorrelation)

**Violation**: Stockpiling during promotions reduces future sales

**Test**: Durbin-Watson statistic, residual ACF plot

**Mitigation**:
- Include lagged promotion variable
- Use robust standard errors (cluster by product or time)

#### 5. No Omitted Variables
**Assumption**: All relevant factors are included in the model

**Violation**: Unobserved marketing activity, shelf placement, competitor actions

**Mitigation**:
- Use fixed effects to absorb time-invariant omitted variables
- Include available controls (holidays, seasonality)

### Limitations

1. **External Validity**: Elasticity estimates are specific to the time period and market analyzed
2. **Short-Term Focus**: Models capture immediate response; long-term elasticity may differ
3. **Aggregation Bias**: Product-level elasticity may mask heterogeneity across customer segments
4. **Supply-Side Factors**: Model assumes supply is perfectly elastic (quantity supplied = quantity demanded)

---

## Interpretation Guidelines

### 1. Magnitude Interpretation
**Elasticity = -1.5**:
- 1% price increase → 1.5% quantity decrease
- 10% price increase → 15% quantity decrease
- Demand is elastic (revenue decreases with price increase)

**Elasticity = -0.6**:
- 1% price increase → 0.6% quantity decrease
- 10% price increase → 6% quantity decrease
- Demand is inelastic (revenue increases with price increase)

### 2. Statistical Significance
**Check p-value**:
- p < 0.05: Elasticity is statistically significant (reject null hypothesis: ε = 0)
- p ≥ 0.05: No evidence of price sensitivity (do not reject null)

**Report confidence intervals**:
```python
conf_int = model.conf_int(alpha=0.05)
elasticity_ci = conf_int.loc['log_price']
print(f"95% CI: [{elasticity_ci[0]:.3f}, {elasticity_ci[1]:.3f}]")
```

### 3. Economic Significance
**Practical implications**:
- |ε| < 0.5: Very inelastic → aggressive pricing power
- 0.5 ≤ |ε| < 1.0: Inelastic → moderate pricing flexibility
- 1.0 ≤ |ε| < 2.0: Elastic → caution with price increases
- |ε| ≥ 2.0: Highly elastic → avoid price increases

### 4. Revenue Implications
**Total Revenue** = Price × Quantity

**Effect of 1% price increase on revenue**:
```
% Change in Revenue = 1% + ε%
```

**Example**:
- If ε = -0.6: Revenue change = 1% + (-0.6%) = +0.4% (revenue increases)
- If ε = -1.5: Revenue change = 1% + (-1.5%) = -0.5% (revenue decreases)

### 5. Comparing Elasticities
**Across products**:
- Higher |ε| → more price-sensitive
- Compare within categories for fair comparison

**Across time periods**:
- Elasticity may change due to market conditions, competition, consumer preferences

---

## Model Selection Criteria

### 1. Goodness of Fit
**R-squared**: Proportion of variance explained (higher is better)
- R² > 0.5: Good fit
- R² < 0.3: Weak fit (consider additional controls)

**Adjusted R-squared**: Penalizes for number of predictors (use for model comparison)

### 2. Information Criteria
**AIC (Akaike Information Criterion)**: Lower is better
**BIC (Bayesian Information Criterion)**: Lower is better, stronger penalty for complexity

```python
print(f"AIC: {model.aic}")
print(f"BIC: {model.bic}")
```

### 3. Residual Diagnostics
**Heteroscedasticity**: Breusch-Pagan test (p < 0.05 indicates heteroscedasticity)
**Autocorrelation**: Durbin-Watson statistic (value near 2 is ideal)
**Normality**: Q-Q plot, Jarque-Bera test

### 4. Economic Plausibility
**Sign check**: Elasticity should be negative (downward-sloping demand)
**Magnitude check**: Typical range is -0.5 to -3.0 for CPG products

### 5. Out-of-Sample Performance
**Hold-out validation**: Fit on 80% of data, test on 20%
**MAPE**: Mean Absolute Percentage Error (lower is better)

```python
from sklearn.metrics import mean_absolute_percentage_error

y_pred = model.predict(X_test)
mape = mean_absolute_percentage_error(np.exp(y_test), np.exp(y_pred))
print(f"MAPE: {mape:.2%}")
```

---

## Implementation Recommendations

### Step-by-Step Workflow

#### 1. Start Simple
- Begin with baseline log-log model (price only)
- Check sign and magnitude of elasticity

#### 2. Add Promotion Control
- Include promotion indicator
- Compare elasticity with and without control

#### 3. Add Time Controls
- Add day-of-week and holiday indicators
- Check if elasticity changes

#### 4. Add Fixed Effects (if applicable)
- Use panel model with product and time fixed effects
- Compare to OLS estimates

#### 5. Validate & Diagnose
- Check residuals for heteroscedasticity and autocorrelation
- Run out-of-sample validation

#### 6. Sensitivity Analysis
- Try alternative specifications (linear, semi-log)
- Vary sample period (full year vs. non-holiday periods)
- Estimate by category or price segment

### Reporting Template

```
Product: [Product Name]
Time Period: [Start Date] to [End Date]
Sample Size: [N observations]

Model: log(Quantity) = β₀ + β₁·log(Price) + β₂·Promotion + Controls

Results:
- Price Elasticity (β₁): -1.23 (SE = 0.15, p < 0.001)
- 95% Confidence Interval: [-1.52, -0.94]
- Interpretation: 1% price increase → 1.23% quantity decrease
- Classification: Elastic demand

Model Fit:
- R²: 0.62
- Adjusted R²: 0.61
- AIC: 1234.5

Validation:
- Out-of-sample MAPE: 8.3%
- Residuals: No significant autocorrelation (DW = 1.98)
```

---

## References

1. **Econometric Theory**:
   - Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel Data*. MIT Press.

2. **Retail Pricing**:
   - Tellis, G. J. (1988). "The Price Elasticity of Selective Demand: A Meta-Analysis of Econometric Models of Sales." *Journal of Marketing Research*.

3. **Panel Data Methods**:
   - Baltagi, B. H. (2013). *Econometric Analysis of Panel Data*. John Wiley & Sons.

---

**Document Version**: 1.0  
**Last Updated**: 2023-12-21  
**Author**: Analytics Team
