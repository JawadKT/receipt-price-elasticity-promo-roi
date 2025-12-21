# Receipt-Driven Price Elasticity & Promo ROI Analyzer

A data science framework for measuring consumer price sensitivity and evaluating promotional effectiveness using transaction-level receipt data.

---

## Table of Contents
- [Problem Statement](#problem-statement)
- [Data Sources](#data-sources)
- [Assumptions](#assumptions)
- [Methodology](#methodology)
- [Key Outputs](#key-outputs)
- [Limitations](#limitations)
- [Future Work](#future-work)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [License](#license)

---

## Problem Statement

### Business Context
Retailers and CPG (Consumer Packaged Goods) brands invest billions annually in promotional activities—discounts, coupons, BOGO offers, and shelf placements. However, many organizations struggle to answer critical questions:

- **How sensitive are consumers to price changes?** Understanding price elasticity helps optimize pricing strategies and revenue.
- **Which promotions drive profitable incremental sales?** Not all promotions yield positive ROI; some merely cannibalize full-price sales.
- **What is the true lift from promotional campaigns?** Measuring incremental impact requires distinguishing baseline demand from promo-driven demand.

### Objective
This project aims to:
1. **Quantify price elasticity** at the product and category level using transaction data
2. **Measure promotional ROI** by calculating incremental revenue, profit, and units sold
3. **Identify optimal promotional strategies** that maximize profitability while maintaining customer value

### Target Audience
- **Pricing Analysts**: Optimize pricing strategies based on demand curves
- **Marketing Teams**: Evaluate promotional effectiveness and budget allocation
- **Category Managers**: Understand cross-product effects and substitution patterns
- **Executives**: Make data-driven decisions on promotional investment

---

## Data Sources

This analysis leverages **transaction-level receipt data** as the primary input. Typical data sources include:

### 1. Receipt/Transaction Data
- **Source**: Point-of-sale (POS) systems, loyalty programs, or receipt aggregators (e.g., Numerator, Nielsen)
- **Key Fields**:
  - Transaction ID, timestamp, store/location ID
  - Product UPC, description, category, brand
  - Unit price, quantity purchased, discount amount
  - Promotion indicator (yes/no), promotion type (coupon, BOGO, % off)
  
### 2. Product Master Data
- **Source**: Internal product catalogs or vendor feeds
- **Key Fields**:
  - Product hierarchy (department → category → subcategory → SKU)
  - MSRP (manufacturer suggested retail price)
  - Cost of goods sold (COGS), margin percentage
  - Package size, unit of measure

### 3. Calendar/External Factors (Optional)
- **Source**: Economic indicators, weather data, competitive activity
- **Key Fields**:
  - Holiday indicators, day of week, seasonality
  - Local unemployment rates, gas prices
  - Competitor pricing and promotional activity

### Data Requirements
- **Time Period**: Minimum 12 months of historical data recommended (24+ months preferred)
- **Volume**: Sufficient transactions per product to enable statistical significance
- **Granularity**: Daily or weekly aggregation for time-series modeling

---

## Assumptions

### Analytical Assumptions
1. **Stable Market Conditions**: Price elasticity is assumed relatively constant over the analysis period, absent major market disruptions
2. **Product Substitutability**: Cross-elasticity effects are limited to defined category boundaries (may not capture all substitution)
3. **Promotion Attribution**: Discounts and promotions are accurately flagged in transaction data; attribution is complete
4. **No Strategic Stockpiling**: Consumers do not significantly stockpile products during promotions (or this effect is quantified separately)
5. **Linear or Log-Linear Demand**: Demand response to price follows parametric forms (linear, log-log, semi-log)

### Data Quality Assumptions
1. **Completeness**: Transaction data captures all relevant sales (no significant gaps or missing periods)
2. **Accuracy**: Prices, quantities, and promotion flags are recorded correctly
3. **Consistency**: Product identifiers (UPCs) are consistent across time and locations
4. **Representative Sample**: If using sampled data, the sample is representative of the target population

### Business Assumptions
1. **Cost Structure**: COGS and promotional costs are known or can be reasonably estimated
2. **Baseline Definition**: Non-promotional periods provide a valid baseline for comparison
3. **Incremental Sales**: Promotional lifts are not solely due to time-shifting (i.e., pulling forward future demand)

---

## Methodology

### 1. Data Preparation
- **Cleaning**: Handle missing values, outliers, and data quality issues
- **Feature Engineering**: 
  - Create price change variables (absolute, percentage, log)
  - Generate promotion indicators and typology
  - Calculate time-based features (week, month, seasonality)
  - Construct competitive and contextual variables
- **Aggregation**: Roll up transactions to product-day or product-week level

### 2. Exploratory Data Analysis (EDA)
- Visualize price distributions and promotional frequency
- Analyze demand patterns over time (seasonality, trends)
- Identify outliers and structural breaks
- Examine correlations between price, promotions, and sales volume

### 3. Price Elasticity Estimation
**Approach**: Econometric modeling using regression techniques

#### Option A: Log-Log Regression (Constant Elasticity)
```
log(Quantity) = β₀ + β₁·log(Price) + β₂·Promo + β₃·Controls + ε
```
- **β₁ = price elasticity** (% change in quantity per 1% change in price)

#### Option B: Fixed Effects Panel Model
```
log(Qᵢₜ) = αᵢ + β₁·log(Pᵢₜ) + β₂·Promoᵢₜ + γ·Xᵢₜ + εᵢₜ
```
- **αᵢ**: Product fixed effects (controls for unobserved heterogeneity)
- **Xᵢₜ**: Time controls, seasonality, external factors

#### Option C: Machine Learning (Random Forest, Gradient Boosting)
- Non-parametric approach to capture non-linear demand curves
- Use SHAP values or partial dependence plots to extract elasticity

**Output**: Product-level and category-level elasticity estimates with confidence intervals

### 4. Promotional ROI Calculation
**Metric Framework**:

1. **Baseline Sales**: Estimate expected sales without promotion (using non-promo periods or counterfactual models)
2. **Incremental Units**: `Actual Sales - Baseline Sales`
3. **Incremental Revenue**: `Incremental Units × Promotional Price`
4. **Promotional Cost**: Discount amount + marketing/execution costs
5. **Incremental Profit**: `(Incremental Revenue × Margin) - Promotional Cost`
6. **ROI**: `(Incremental Profit / Promotional Cost) × 100%`

**Baseline Estimation Methods**:
- **Pre-Post Comparison**: Compare promotional weeks to non-promotional weeks (adjusted for seasonality)
- **Difference-in-Differences**: Use control products/stores not exposed to promotion
- **Synthetic Control**: Construct synthetic counterfactual using similar products
- **Time Series Forecasting**: Use ARIMA, Prophet, or ML models to predict baseline

### 5. Segmentation & Targeting
- Segment products by elasticity (elastic vs. inelastic)
- Identify high-ROI promotional tactics by product category
- Analyze customer segments (if loyalty data available)

### 6. Optimization Recommendations
- Simulate pricing scenarios using elasticity estimates
- Recommend optimal discount depths and promotional frequency
- Identify products where promotions destroy value (negative ROI)

---

## Key Outputs

### 1. Price Elasticity Metrics
- **Product-level elasticity coefficients** (e.g., "1% price increase → X% quantity decrease")
- **Category-level elasticity benchmarks**
- **Segmentation**: Elastic products (|ε| > 1) vs. inelastic products (|ε| < 1)
- **Cross-elasticity matrix** (optional): How price changes in Product A affect demand for Product B

### 2. Promotional ROI Dashboard
- **Summary Metrics**:
  - Total promotional spend and incremental profit
  - Portfolio-level ROI percentage
  - Promotion effectiveness by type (% off, BOGO, coupon, etc.)
- **Product-Level ROI**:
  - Table ranking products by ROI (high to low)
  - Identification of value-destroying promotions (ROI < 0%)
- **Time Series View**: ROI trends over time, seasonality effects

### 3. Strategic Recommendations
- **Pricing Optimization**:
  - Suggested price adjustments for revenue maximization
  - Products suitable for price increases (inelastic demand)
- **Promotional Strategy**:
  - High-ROI promotional tactics to scale
  - Low-ROI promotions to reduce or eliminate
  - Optimal discount depths (e.g., 15% vs. 25% off)
- **Category Insights**: Cross-product effects, basket complementarity

### 4. Visualizations & Reports
- **Demand Curves**: Price vs. quantity plots with elasticity overlays
- **ROI Waterfall Charts**: Breakdown of incremental revenue, cost, and profit
- **Heatmaps**: Elasticity by category and time period
- **Executive Summary**: 1-2 page PDF with key findings and recommendations

---

## Limitations

### Data Limitations
1. **Sample Bias**: Receipt data may not represent all customers (e.g., excludes non-loyalty members)
2. **Missing Variables**: Unobserved factors (competitor actions, advertising, shelf placement) may confound results
3. **Aggregation**: Product-level analysis may mask heterogeneity across customer segments or store formats
4. **Time Lag**: Promotional effects may extend beyond immediate transaction (repeat purchases, brand switching)

### Methodological Limitations
1. **Endogeneity**: Prices and promotions are not randomly assigned; retailers may discount slow-moving products (reverse causality)
2. **Omitted Variable Bias**: Failure to control for all relevant factors may bias elasticity estimates
3. **Functional Form**: Assumed demand curve shape (log-log, linear) may not fit all products
4. **External Validity**: Elasticity estimates are context-specific and may not generalize to different time periods, markets, or competitive landscapes

### Business Limitations
1. **Short-Term Focus**: Analysis captures immediate promotional lift but may miss long-term effects (brand equity, customer lifetime value)
2. **Cannibalization**: Difficult to fully isolate whether promotional sales steal from other products or future periods
3. **Stockpiling**: Promotions may induce pantry loading, inflating short-term ROI but reducing future demand
4. **Cost Allocation**: Promotional costs (especially fixed costs like ad campaigns) are challenging to allocate to individual SKUs

### Implementation Limitations
1. **Organizational Alignment**: Pricing and promotional decisions involve multiple stakeholders (finance, marketing, operations)
2. **System Constraints**: Legacy pricing systems may lack flexibility for dynamic or personalized pricing
3. **Competitive Response**: Optimal pricing assumes competitors hold prices constant, which may not hold in practice

---

## Future Work

### Enhancements to Current Analysis
1. **Cross-Elasticity Modeling**: Expand to capture substitution and complementarity effects across products
2. **Customer Segmentation**: Incorporate household-level data to estimate elasticity by customer segment (high vs. low spenders, loyal vs. switchers)
3. **Causal Inference**: Implement instrumental variable (IV) or regression discontinuity designs to address endogeneity
4. **Dynamic Pricing**: Model intertemporal effects (e.g., how today's promotion affects next week's demand)
5. **Bayesian Methods**: Use hierarchical Bayesian models to pool information across similar products and improve estimates for low-volume SKUs

### Advanced Techniques
1. **Deep Learning for Demand Forecasting**: Use LSTM or Transformer models to capture complex temporal patterns
2. **Reinforcement Learning**: Train RL agents to learn optimal pricing and promotional policies via simulation
3. **Uplift Modeling**: Predict individual customer response to promotions (who needs a discount vs. who would buy anyway)
4. **Multi-Touch Attribution**: Allocate promotional impact across multiple touchpoints (email, in-store display, coupon)

### Data Expansion
1. **External Data Integration**:
   - Weather data (e.g., ice cream sales on hot days)
   - Economic indicators (unemployment, consumer confidence)
   - Social media sentiment and trending products
2. **Competitive Intelligence**: Scrape competitor pricing and promotional activity
3. **Marketing Mix Modeling (MMM)**: Integrate advertising spend, TV/digital impressions, and store traffic data

### Product Features
1. **Real-Time Dashboard**: Deploy elasticity and ROI metrics in a live BI tool (Tableau, Power BI, Streamlit)
2. **Automated Alerting**: Flag products with deteriorating ROI or unexpected elasticity shifts
3. **A/B Testing Framework**: Design and analyze randomized pricing experiments
4. **API Development**: Expose elasticity estimates via REST API for integration with pricing engines
5. **Personalized Pricing**: Use elasticity estimates to tailor offers at the customer level (if legally and ethically permissible)

### Organizational Enablement
1. **Playbooks**: Develop operational guidelines for pricing and promotional decision-making
2. **Training**: Educate stakeholders on interpreting elasticity metrics and ROI outputs
3. **Governance**: Establish approval workflows and guardrails for pricing changes
4. **Continuous Learning**: Implement feedback loops to refine models as new data arrives

---

## Project Structure

```
receipt-price-elasticity-promo-roi/
├── src/                    # Source code for the project
│   ├── data/              # Data loading and preprocessing scripts
│   ├── features/          # Feature engineering and transformation
│   ├── models/            # Model training, evaluation, and prediction
│   └── visualization/     # Plotting and visualization utilities
├── notebooks/             # Jupyter notebooks for exploration and analysis
├── reports/               # Generated analysis reports and presentations
│   ├── figures/          # Graphics and figures for reporting
│   └── tables/           # Generated tables and summary statistics
├── data/                  # Project data (see .gitignore for exclusions)
│   ├── raw/              # Original, immutable data (gitignored)
│   ├── processed/        # Final, canonical datasets for modeling
│   ├── interim/          # Intermediate transformed data
│   └── sample/           # Sample/dummy data for testing (tracked in git)
├── tests/                 # Unit and integration tests
├── config/                # Configuration files (YAML, JSON, etc.)
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
└── .gitignore            # Git ignore rules
```

## Folder Descriptions

### `src/`
Contains all production-ready Python modules and packages:
- **data/**: Scripts for data ingestion, cleaning, and validation
- **features/**: Feature engineering pipelines and transformations
- **models/**: Model implementations, training routines, and evaluation metrics
- **visualization/**: Reusable plotting functions and dashboard generation

### `notebooks/`
Jupyter notebooks for exploratory data analysis (EDA), experimentation, and prototyping. Use naming convention: `01_descriptive_name.ipynb`

### `reports/`
Generated analysis outputs, presentations, and documentation:
- **figures/**: PNG, PDF, or SVG files for reports and papers
- **tables/**: CSV or Excel files with summary statistics and results

### `data/`
Project datasets at various stages:
- **raw/**: Original, unmodified data (not tracked in git for privacy/size)
- **processed/**: Clean, final datasets ready for modeling
- **interim/**: Intermediate data that has been transformed
- **sample/**: Small sample datasets for testing (tracked in git)

### `tests/`
Unit tests and integration tests for code in `src/`

### `config/`
Configuration files for model parameters, database connections, API keys, etc.

### `docs/`
Additional documentation, methodology notes, and technical specifications

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Add your raw data to `data/raw/`

3. Run data preprocessing:
   ```bash
   python src/data/preprocess.py
   ```

## License

[Your License Here]
