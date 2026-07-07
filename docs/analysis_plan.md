# Analysis Plan: Receipt-Based Price Elasticity & Promotion ROI

This document provides a step-by-step methodology for conducting price elasticity and promotional ROI analysis using transaction-level receipt data.

---

## Table of Contents

1. [Project Setup & Environment](#1-project-setup--environment)
2. [Data Ingestion & Validation](#2-data-ingestion--validation)
3. [Exploratory Data Analysis (EDA)](#3-exploratory-data-analysis-eda)
4. [Data Preprocessing & Feature Engineering](#4-data-preprocessing--feature-engineering)
5. [Price Elasticity Estimation](#5-price-elasticity-estimation)
6. [Promotional ROI Calculation](#6-promotional-roi-calculation)
7. [Model Validation & Diagnostics](#7-model-validation--diagnostics)
8. [Results Synthesis & Insights](#8-results-synthesis--insights)
9. [Strategic Recommendations](#9-strategic-recommendations)
10. [Documentation & Delivery](#10-documentation--delivery)

---

## 1. Project Setup & Environment

### 1.1 Define Business Objectives
- **Primary Question**: What is the price elasticity of demand for our product portfolio?
- **Secondary Question**: Which promotions generate positive ROI and should be scaled?
- **Stakeholders**: Pricing team, marketing, category managers, finance
- **Success Metrics**: 
  - Elasticity estimates with confidence intervals for top 80% of revenue
  - ROI calculated for 100% of promotional events
  - Actionable recommendations on 5-10 key products/categories

### 1.2 Set Up Development Environment
```bash
# Clone repository
git clone <repo_url>
cd receipt-price-elasticity-promo-roi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 1.3 Establish Data Governance
- **Data Access**: Confirm access to POS/receipt data sources
- **Privacy Compliance**: Ensure GDPR/CCPA compliance if customer data is included
- **Data Security**: Store raw data in secure location (never commit to git)
- **Backup Strategy**: Daily backups of processed data and model outputs

### 1.4 Define Analysis Scope
- **Time Period**: 12-24 months (minimum for seasonality)
- **Product Scope**: Focus on top categories by revenue (e.g., top 20%)
- **Geographic Scope**: All stores or specific regions?
- **Exclusions**: Clearance items, discontinued products, extreme outliers

---

## 2. Data Ingestion & Validation

### 2.1 Load Raw Data
**Script**: `src/data/load_data.py`

```python
# Pseudocode
import pandas as pd

# Load receipt line-item data
receipts = pd.read_csv('data/raw/receipt_data.csv', 
                        parse_dates=['transaction_timestamp'])

# Load product master data
products = pd.read_csv('data/raw/product_master.csv')

# Load store master data
stores = pd.read_csv('data/raw/store_master.csv')
```

**Deliverable**: Raw data loaded into pandas DataFrames or database

### 2.2 Initial Data Profiling
**Notebook**: `notebooks/01_data_profiling.ipynb`

Generate summary statistics:
- Row counts, null percentages, data types
- Unique values for categorical fields
- Min/max/median for numeric fields
- Date range coverage

**Tools**: `pandas-profiling`, `ydata-profiling`, or custom functions

**Deliverable**: Data quality report highlighting major issues

### 2.3 Data Quality Validation
**Script**: `src/data/validate_data.py`

Implement validation checks:
```python
# Check primary key uniqueness
assert receipts[['transaction_id', 'line_item_id']].duplicated().sum() == 0

# Check non-null critical fields
critical_fields = ['transaction_id', 'transaction_date', 'upc', 'quantity', 'final_price']
for field in critical_fields:
    assert receipts[field].notna().all(), f"{field} has null values"

# Check logical constraints
assert (receipts['quantity'] > 0).all() or receipts['is_return'].notna().any()
assert (receipts['final_price'] >= 0).all()

# Check date ranges
assert receipts['transaction_date'].max() <= pd.Timestamp.today()
```

**Deliverable**: Validated dataset with flagged issues for remediation

### 2.4 Join Master Data
**Script**: `src/data/join_master_data.py`

```python
# Enrich receipts with product metadata
receipts_enriched = receipts.merge(
    products[['upc', 'category', 'subcategory', 'brand', 'package_size']],
    on='upc',
    how='left',
    validate='m:1'
)

# Enrich with store metadata
receipts_enriched = receipts_enriched.merge(
    stores[['store_id', 'store_format', 'region']],
    on='store_id',
    how='left',
    validate='m:1'
)
```

**Deliverable**: Enriched receipt dataset saved to `data/interim/receipts_enriched.parquet`

---

## 3. Exploratory Data Analysis (EDA)

### 3.1 Sales Volume Analysis
**Notebook**: `notebooks/02_exploratory_analysis.ipynb`

**Analyses**:
1. **Time Series**: Daily/weekly sales volume trends
2. **Seasonality**: Day-of-week effects, monthly patterns, holiday spikes
3. **Category Performance**: Revenue and unit sales by category
4. **Top Products**: Pareto analysis (80/20 rule)

**Visualizations**:
- Line charts: Sales over time
- Heatmaps: Sales by day-of-week and week-of-year
- Bar charts: Top 20 products/categories

**Key Questions**:
- Are there structural breaks (e.g., COVID-19, supply chain issues)?
- Which products have sufficient transaction volume for elasticity estimation?

### 3.2 Price Distribution Analysis

**Analyses**:
1. **Price Variation**: Distribution of `final_price` by product
2. **Price Changes**: Frequency and magnitude of price changes over time
3. **Discount Depth**: Distribution of `discount_percentage`
4. **Regular vs. Promotional**: Compare price distributions

**Visualizations**:
- Histograms: Price distributions by product/category
- Box plots: Price variation across stores/regions
- Scatter plots: Price vs. quantity sold

**Key Questions**:
- Is there sufficient price variation to estimate elasticity?
- Are prices stable or highly volatile?

### 3.3 Promotional Activity Analysis

**Analyses**:
1. **Promotion Frequency**: % of transactions with promotions by category
2. **Promotion Types**: Mix of BOGO, % off, coupons, etc.
3. **Promotional Lift**: Average quantity increase during promotions
4. **Baseline vs. Promo**: Sales comparison

**Visualizations**:
- Pie chart: Promotion type distribution
- Bar chart: Promotional frequency by category
- Time series: Promotional events overlaid on sales

**Key Questions**:
- Are promotions concentrated in certain periods (holiday seasons)?
- Do promotions show obvious lift in unit sales?

### 3.4 Identify Outliers & Anomalies

**Analyses**:
1. **Statistical Outliers**: Z-scores or IQR method for quantity and price
2. **Anomalous Transactions**: Very large baskets, returns, voided items
3. **Data Entry Errors**: Prices of $0.01, quantities in the thousands

**Action**: Flag outliers for removal or capping

**Deliverable**: Summary of EDA findings with key insights and data quality issues

---

## 4. Data Preprocessing & Feature Engineering

### 4.1 Handle Missing Values
**Script**: `src/data/handle_missing.py`

**Strategies**:
- **regular_price**: Impute with median price per product (non-promo periods)
- **promotion_type**: Fill with "None" if `is_promotion = FALSE`
- **category/brand**: Drop rows if critical for analysis, otherwise flag

### 4.2 Filter & Clean Data
**Script**: `src/data/clean_data.py`

**Cleaning Steps**:
1. **Remove Returns**: Filter out `is_return = TRUE` (or analyze separately)
2. **Remove Outliers**: Cap quantities at 99th percentile per product
3. **Remove Invalid Prices**: Drop rows with `final_price <= 0` (unless returns)
4. **Remove Low-Volume Products**: Keep products with at least 30 observations
5. **Deduplicate**: Remove exact duplicates

### 4.3 Feature Engineering
**Script**: `src/features/build_features.py`

**Price Features**:
```python
# Log-transformed prices (for log-log regression)
df['log_price'] = np.log(df['final_price'])
df['log_quantity'] = np.log(df['quantity'])

# Price change from regular price
df['price_change_pct'] = (df['final_price'] - df['regular_price']) / df['regular_price']

# Discount depth
df['discount_pct'] = (df['discount_amount'] / df['regular_price']) * 100
```

**Temporal Features**:
```python
# Calendar features
df['day_of_week'] = df['transaction_date'].dt.dayofweek
df['week_of_year'] = df['transaction_date'].dt.isocalendar().week
df['month'] = df['transaction_date'].dt.month
df['quarter'] = df['transaction_date'].dt.quarter
df['is_weekend'] = df['day_of_week'].isin([5, 6])

# Holiday flags (requires external calendar)
df['is_holiday'] = df['transaction_date'].isin(holiday_dates)
df['is_holiday_week'] = df['week_of_year'].isin(holiday_weeks)
```

**Promotional Features**:
```python
# Binary promotion indicator
df['promo_binary'] = (df['is_promotion']).astype(int)

# Promotion type dummies
df = pd.get_dummies(df, columns=['promotion_type'], prefix='promo')

# Lagged promotions (did product have promo in prior week?)
df['promo_lag1'] = df.groupby('upc')['promo_binary'].shift(1)
```

**Product Features**:
```python
# Category dummies
df = pd.get_dummies(df, columns=['category'], prefix='cat')

# Average product price (over all time)
df['avg_product_price'] = df.groupby('upc')['final_price'].transform('mean')

# Price relative to average
df['price_index'] = df['final_price'] / df['avg_product_price']
```

**Deliverable**: Feature-engineered dataset saved to `data/processed/receipts_features.parquet`

### 4.4 Aggregate to Product-Period Level
**Script**: `src/data/aggregate_data.py`

**Aggregation**:
```python
# Aggregate to product-week level
agg_data = df.groupby(['upc', 'product_name', 'category', 'week', 'year']).agg({
    'quantity': 'sum',
    'final_price': 'mean',
    'regular_price': 'mean',
    'discount_amount': 'sum',
    'line_total': 'sum',
    'promo_binary': 'max',  # Was there any promo this week?
    'transaction_id': 'nunique'  # Number of transactions
}).reset_index()

# Rename columns
agg_data.rename(columns={'transaction_id': 'num_transactions'}, inplace=True)
```

**Deliverable**: Aggregated dataset saved to `data/processed/product_week_aggregated.parquet`

---

## 5. Price Elasticity Estimation

### 5.1 Select Modeling Approach

**Options**:
1. **Simple Log-Log Regression** (constant elasticity)
2. **Fixed Effects Panel Regression** (control for product heterogeneity)
3. **Machine Learning** (Random Forest, Gradient Boosting with SHAP)

**Recommendation**: Start with log-log regression for interpretability, validate with fixed effects

### 5.2 Estimate Elasticity - Log-Log Model
**Script**: `src/models/elasticity_log_log.py`

**Model Specification**:
```
log(Quantity) = β₀ + β₁·log(Price) + β₂·Promo + β₃·Weekend + β₄·Holiday + ε
```

**Implementation**:
```python
import statsmodels.api as sm

# Prepare data
model_data = agg_data[agg_data['quantity'] > 0].copy()
model_data['log_quantity'] = np.log(model_data['quantity'])
model_data['log_price'] = np.log(model_data['final_price'])

# Define variables
X = model_data[['log_price', 'promo_binary', 'is_weekend', 'is_holiday']]
X = sm.add_constant(X)
y = model_data['log_quantity']

# Fit model
model = sm.OLS(y, X).fit()
print(model.summary())

# Extract elasticity
price_elasticity = model.params['log_price']
```

**Run for Each Product**:
```python
elasticities = {}
for upc in top_products:
    product_data = model_data[model_data['upc'] == upc]
    if len(product_data) >= 30:  # Minimum observations
        model = fit_elasticity_model(product_data)
        elasticities[upc] = {
            'elasticity': model.params['log_price'],
            'std_error': model.bse['log_price'],
            'pvalue': model.pvalues['log_price'],
            'r_squared': model.rsquared
        }
```

**Deliverable**: Elasticity estimates saved to `data/processed/elasticity_estimates.csv`

### 5.3 Estimate Elasticity - Fixed Effects Model
**Script**: `src/models/elasticity_fixed_effects.py`

**Model Specification**:
```
log(Qᵢₜ) = αᵢ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + γ·Timeₜ + εᵢₜ
```

**Implementation**:
```python
from linearmodels.panel import PanelOLS

# Set up panel data
panel_data = model_data.set_index(['upc', 'week'])

# Fit fixed effects model
fe_model = PanelOLS.from_formula(
    'log_quantity ~ log_price + promo_binary + EntityEffects',
    data=panel_data
).fit(cov_type='clustered', cluster_entity=True)

print(fe_model.summary)
```

**Deliverable**: Category-level elasticity with fixed effects saved to `data/processed/elasticity_fe.csv`

### 5.4 Estimate Elasticity - Machine Learning
**Script**: `src/models/elasticity_ml.py`

**Approach**:
```python
from sklearn.ensemble import RandomForestRegressor
import shap

# Features
features = ['final_price', 'promo_binary', 'is_weekend', 'is_holiday', 
            'avg_product_price', 'day_of_week']
X = model_data[features]
y = model_data['quantity']

# Train model
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X, y)

# SHAP values for price elasticity interpretation
explainer = shap.TreeExplainer(rf_model)
shap_values = explainer.shap_values(X)

# Partial dependence plot for price
from sklearn.inspection import PartialDependenceDisplay
PartialDependenceDisplay.from_estimator(rf_model, X, ['final_price'])
```

**Deliverable**: ML-based elasticity interpretations and plots saved to `reports/figures/`

### 5.5 Categorize Products by Elasticity

**Segmentation**:
- **Highly Elastic** (|ε| > 1.5): Quantity very sensitive to price
- **Elastic** (1.0 < |ε| ≤ 1.5): Moderate sensitivity
- **Unit Elastic** (|ε| ≈ 1.0): Proportional response
- **Inelastic** (|ε| < 1.0): Low sensitivity
- **Not Significant**: p-value > 0.05

**Deliverable**: Elasticity segmentation table saved to `reports/tables/elasticity_segments.csv`

---

## 6. Promotional ROI Calculation

### 6.1 Define Baseline (Counterfactual)
**Script**: `src/models/baseline_estimation.py`

**Method 1: Non-Promotional Average**
```python
# Calculate average sales during non-promo periods
baseline = agg_data[agg_data['promo_binary'] == 0].groupby('upc')['quantity'].mean()
```

**Method 2: Time Series Forecasting**
```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Fit on non-promo periods, predict for promo periods
non_promo = agg_data[agg_data['promo_binary'] == 0]
model = ExponentialSmoothing(non_promo['quantity'], seasonal_periods=52, 
                             trend='add', seasonal='add').fit()
baseline_forecast = model.forecast(steps=len(promo_periods))
```

**Method 3: Difference-in-Differences**
```python
# Compare promoted products to similar non-promoted products
# (Requires control group)
```

**Deliverable**: Baseline sales estimates saved to `data/processed/baseline_sales.csv`

### 6.2 Calculate Incremental Metrics
**Script**: `src/models/calculate_roi.py`

**ROI Framework**:
```python
# For each promotional event
promo_data = agg_data[agg_data['promo_binary'] == 1].copy()

# Merge baseline
promo_data = promo_data.merge(baseline, on='upc', suffixes=('_actual', '_baseline'))

# Calculate incremental units
promo_data['incremental_units'] = promo_data['quantity_actual'] - promo_data['quantity_baseline']

# Calculate incremental revenue
promo_data['incremental_revenue'] = promo_data['incremental_units'] * promo_data['final_price']

# Calculate promotional cost
promo_data['promo_cost'] = promo_data['discount_amount']

# Calculate incremental profit (assuming margin)
promo_data['margin'] = 0.30  # Example: 30% margin (should be product-specific)
promo_data['incremental_profit'] = (promo_data['incremental_revenue'] * promo_data['margin']) - promo_data['promo_cost']

# Calculate ROI
promo_data['roi'] = (promo_data['incremental_profit'] / promo_data['promo_cost']) * 100
```

**Deliverable**: Promotional ROI results saved to `data/processed/promo_roi.csv`

### 6.3 Aggregate ROI by Promotion Type

**Analysis**:
```python
# ROI by promotion type
roi_by_type = promo_data.groupby('promotion_type').agg({
    'roi': 'mean',
    'incremental_profit': 'sum',
    'promo_cost': 'sum',
    'incremental_units': 'sum'
}).reset_index()

# ROI by category
roi_by_category = promo_data.groupby('category').agg({
    'roi': 'mean',
    'incremental_profit': 'sum',
    'promo_cost': 'sum'
}).reset_index()
```

**Deliverable**: Aggregated ROI tables saved to `reports/tables/`

### 6.4 Identify High & Low Performers

**Segmentation**:
- **High ROI** (ROI > 50%): Scale these promotions
- **Positive ROI** (0% < ROI ≤ 50%): Maintain or optimize
- **Break-Even** (ROI ≈ 0%): Evaluate strategic value
- **Negative ROI** (ROI < 0%): Reduce or eliminate

**Deliverable**: Product-level ROI segmentation saved to `reports/tables/roi_segments.csv`

---

## 7. Model Validation & Diagnostics

### 7.1 Regression Diagnostics
**Notebook**: `notebooks/03_model_diagnostics.ipynb`

**Checks**:
1. **Residual Analysis**: Plot residuals vs. fitted values (check for heteroscedasticity)
2. **Normality**: Q-Q plot of residuals
3. **Multicollinearity**: VIF (Variance Inflation Factor) for independent variables
4. **Autocorrelation**: Durbin-Watson test for time series data

**Action**: Address issues with robust standard errors, transformations, or alternative models

### 7.2 Out-of-Sample Validation

**Train-Test Split**:
```python
# Split data temporally (last 3 months as test set)
train = model_data[model_data['transaction_date'] < '2023-10-01']
test = model_data[model_data['transaction_date'] >= '2023-10-01']

# Fit model on training data
model_train = fit_elasticity_model(train)

# Predict on test data
test['predicted_quantity'] = predict_quantity(model_train, test)

# Evaluate
from sklearn.metrics import mean_absolute_percentage_error
mape = mean_absolute_percentage_error(test['quantity'], test['predicted_quantity'])
print(f"MAPE: {mape:.2%}")
```

**Deliverable**: Validation metrics and plots saved to `reports/figures/`

### 7.3 Sensitivity Analysis

**Questions**:
- How do elasticity estimates change with different time windows?
- How sensitive is ROI to margin assumptions?
- What if baseline is calculated differently?

**Action**: Run analysis with alternative assumptions and document ranges

### 7.4 Sanity Checks

**Business Logic Validation**:
- Are elasticity estimates reasonable? (Typically between -0.5 and -3.0)
- Do inelastic products make sense? (e.g., milk, eggs, staples)
- Do elastic products make sense? (e.g., premium brands, discretionary items)
- Are high-ROI promotions aligned with business intuition?

**Deliverable**: Validation summary in `reports/model_validation_report.md`

---

## 8. Results Synthesis & Insights

### 8.1 Create Elasticity Summary Dashboard
**Notebook**: `notebooks/04_results_visualization.ipynb`

**Visualizations**:
1. **Elasticity Distribution**: Histogram of elasticity values
2. **Elasticity Heatmap**: By category and subcategory
3. **Top 10 Elastic Products**: Bar chart
4. **Top 10 Inelastic Products**: Bar chart
5. **Demand Curves**: Price vs. quantity scatter with fitted curves (top products)

**Tools**: `matplotlib`, `seaborn`, `plotly`

**Deliverable**: Dashboard saved as `reports/elasticity_dashboard.html` or `reports/figures/`

### 8.2 Create ROI Summary Dashboard

**Visualizations**:
1. **ROI Distribution**: Histogram
2. **ROI by Promotion Type**: Bar chart
3. **ROI by Category**: Horizontal bar chart
4. **ROI Waterfall**: Breakdown of revenue, cost, profit for portfolio
5. **Time Series**: ROI trends over time

**Deliverable**: Dashboard saved as `reports/roi_dashboard.html`

### 8.3 Generate Key Insights

**Elasticity Insights**:
- "Category X has high elasticity (-2.3), indicating strong price sensitivity. Price increases should be avoided."
- "Category Y is inelastic (-0.6), presenting opportunities for price optimization."
- "Premium brands show higher elasticity than private label, suggesting brand loyalty is weaker at higher price points."

**ROI Insights**:
- "BOGO promotions generate 85% ROI on average, significantly outperforming % off discounts (12% ROI)."
- "Product A has negative ROI (-15%) across all promotional types—promotions should be eliminated."
- "Q4 holiday promotions show 2x higher ROI than Q2 summer promotions."

**Deliverable**: Insights document saved to `reports/key_insights.md`

---

## 9. Strategic Recommendations

### 9.1 Pricing Optimization Recommendations
**Notebook**: `notebooks/05_pricing_recommendations.ipynb`

**Framework**:
```python
# Simulate revenue impact of price changes
def simulate_price_change(product, elasticity, current_price, price_change_pct):
    new_price = current_price * (1 + price_change_pct)
    quantity_change = elasticity * price_change_pct
    new_quantity = current_quantity * (1 + quantity_change)
    new_revenue = new_price * new_quantity
    return new_revenue - current_revenue

# Test scenarios: +5%, +10%, -5%, -10%
scenarios = [-0.10, -0.05, 0.05, 0.10]
for pct in scenarios:
    revenue_impact = simulate_price_change(product, elasticity, current_price, pct)
    print(f"Price change {pct:.0%}: Revenue impact ${revenue_impact:,.0f}")
```

**Recommendations by Elasticity**:
- **Inelastic Products** (|ε| < 1): Consider price increases of 3-5%
- **Elastic Products** (|ε| > 1): Avoid price increases; focus on volume
- **Competitive Products**: Monitor competitor pricing closely

**Deliverable**: Pricing recommendation table saved to `reports/tables/pricing_recommendations.csv`

### 9.2 Promotional Optimization Recommendations

**High-Level Strategies**:
1. **Scale High-ROI Tactics**: Increase frequency/budget for BOGO, tiered discounts
2. **Optimize Discount Depth**: Test 10%, 15%, 20% to find optimal point (not always deeper = better)
3. **Eliminate Negative-ROI Promotions**: Phase out promotions on specific products
4. **Improve Targeting**: Use customer segmentation to target promotions at price-sensitive shoppers
5. **Timing**: Concentrate promotions in high-traffic periods (holidays, weekends)

**Product-Specific Tactics**:
- **Product A**: Reduce discount from 25% to 15% (elasticity suggests diminishing returns)
- **Product B**: Increase promotional frequency from monthly to bi-weekly (underutilized, high ROI)
- **Product C**: Eliminate all promotions (negative ROI, cannibalization suspected)

**Deliverable**: Promotional playbook saved to `reports/promotional_playbook.md`

### 9.3 Category Management Recommendations

**Cross-Elasticity Insights** (if calculated):
- "Promotions on Brand X soda increase sales of Brand Y chips by 15% (complementary products)"
- "Discounting private label milk reduces branded milk sales by 30% (substitution effect)"

**Recommendations**:
- Bundle complementary products for basket-building
- Carefully manage private label vs. branded promotions to avoid cannibalization

### 9.4 Testing & Experimentation Plan

**Proposed A/B Tests**:
1. **Price Test**: Increase price by 5% in test stores for inelastic products
2. **Promotion Test**: Compare 15% vs. 20% discount depth
3. **Timing Test**: Mid-week vs. weekend promotional launches
4. **Channel Test**: In-store vs. loyalty app exclusive offers

**Deliverable**: Experimentation roadmap saved to `reports/testing_roadmap.md`

---

## 10. Documentation & Delivery

### 10.1 Executive Summary
**Document**: `reports/executive_summary.md`

**Contents** (1-2 pages):
- **Objective**: Brief restatement of business question
- **Key Findings**: 3-5 bullet points (e.g., "Portfolio-wide promotional ROI is 42%")
- **Top Recommendations**: 3-5 actionable next steps
- **Impact Estimate**: Projected revenue/profit impact of recommendations

**Format**: Markdown + PDF export for distribution

### 10.2 Technical Report
**Document**: `reports/technical_report.md`

**Contents** (10-20 pages):
- Methodology overview
- Data sources and sample size
- Model specifications and results
- Validation and diagnostics
- Detailed findings by category/product
- Appendix: Full regression tables, diagnostic plots

**Audience**: Data science team, advanced analytics stakeholders

### 10.3 Presentation Deck
**Document**: `reports/presentation.pptx` or Google Slides

**Slides**:
1. Title & Agenda
2. Business Context & Objectives
3. Data Overview & Methodology
4. Key Finding 1: Elasticity Summary
5. Key Finding 2: ROI Summary
6. Deep Dive: High-ROI Opportunities
7. Deep Dive: Negative-ROI Issues
8. Recommendations Summary
9. Implementation Roadmap
10. Q&A / Appendix

**Deliverable**: Presentation file ready for stakeholder meeting

### 10.4 Code & Reproducibility

**Checklist**:
- [ ] All scripts are documented with docstrings
- [ ] Notebooks are cleaned and outputs are cleared (or selectively saved)
- [ ] README includes instructions to reproduce analysis
- [ ] requirements.txt is up-to-date
- [ ] Key outputs (CSVs, figures) are saved to `reports/`
- [ ] Git repository is tagged with version (e.g., `v1.0.0`)

### 10.5 Knowledge Transfer

**Activities**:
1. **Walkthrough Session**: 1-hour session with pricing/marketing teams
2. **Documentation Handoff**: Share technical report and code repository
3. **Training**: How to interpret elasticity estimates and ROI metrics
4. **Support Plan**: Define ongoing support (e.g., monthly model refresh)

---

## Appendix: Tools & Libraries

### Python Libraries
- **Data Manipulation**: `pandas`, `numpy`
- **Visualization**: `matplotlib`, `seaborn`, `plotly`
- **Statistical Modeling**: `statsmodels`, `linearmodels` (fixed effects)
- **Machine Learning**: `scikit-learn`, `xgboost`, `shap`
- **Time Series**: `statsmodels.tsa`, `prophet`
- **Reporting**: `jupyter`, `nbconvert`, `python-pptx`

### Alternative Tools
- **R**: `lm()`, `plm` package for panel data, `ggplot2` for visualization
- **SQL**: For data extraction and aggregation
- **Tableau/Power BI**: For interactive dashboards
- **Excel**: For ad-hoc analysis and stakeholder communication

---

## Appendix: Timeline Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Project Setup | 1-2 days | Data access approved |
| 2. Data Ingestion & Validation | 3-5 days | Raw data available |
| 3. EDA | 3-5 days | Validated data |
| 4. Preprocessing & Feature Engineering | 5-7 days | EDA complete |
| 5. Elasticity Estimation | 5-7 days | Features ready |
| 6. ROI Calculation | 3-5 days | Baseline defined |
| 7. Model Validation | 2-3 days | Models fit |
| 8. Results Synthesis | 3-5 days | All analyses complete |
| 9. Recommendations | 2-3 days | Insights validated |
| 10. Documentation & Delivery | 3-5 days | Stakeholder review |
| **Total** | **4-6 weeks** | |

*Note: Timeline assumes full-time commitment. Part-time work will extend duration proportionally.*

---

## References & Further Reading

1. **Price Elasticity**:
   - Tellis, G. J. (1988). "The Price Elasticity of Selective Demand: A Meta-Analysis of Econometric Models of Sales." *Journal of Marketing Research*.
   
2. **Promotional ROI**:
   - Gupta, S., & Cooper, L. G. (1992). "The Discounting of Discounts and Promotion Thresholds." *Journal of Consumer Research*.

3. **Causal Inference**:
   - Angrist, J. D., & Pischke, J.-S. (2009). *Mostly Harmless Econometrics*. Princeton University Press.

4. **Retail Analytics**:
   - Leeflang, P. S., et al. (2015). *Modeling Markets: Analyzing Marketing Phenomena and Improving Marketing Decision Making*. Springer.

---

**Document Version**: 1.0  
**Last Updated**: 2023-12-21  
**Author**: Analytics Team
