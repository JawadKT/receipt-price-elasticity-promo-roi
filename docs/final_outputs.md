# Final Outputs & Visualizations

This document defines the tables, charts, and metrics that will be produced for business stakeholders.

---

## Table of Contents

1. [Executive Dashboard](#executive-dashboard)
2. [Price Elasticity Outputs](#price-elasticity-outputs)
3. [Promotional ROI Outputs](#promotional-roi-outputs)
4. [Strategic Recommendations](#strategic-recommendations)
5. [Technical Appendix](#technical-appendix)

---

## Executive Dashboard

### 1. One-Page Summary (PDF)
**File**: `reports/executive_summary.pdf`

**Content**:
- **Headline Metrics** (3-4 KPIs in callout boxes):
  - Portfolio-wide promotional ROI: **+42%**
  - Average price elasticity: **-1.15**
  - Products analyzed: **250** (covering **87% of revenue**)
  - High-ROI promotions identified: **12**

- **Key Findings** (3-5 bullet points):
  - "BOGO promotions generate 85% ROI, outperforming % off discounts (12% ROI)"
  - "Beverage category is highly elastic (-1.8), while dairy is inelastic (-0.5)"
  - "15% of promotions have negative ROI and should be eliminated"

- **Top Recommendations** (3-5 action items):
  - Scale BOGO promotions for Product A and Product B
  - Eliminate negative-ROI promotions on Product C
  - Increase prices 3-5% on inelastic products (milk, eggs)

---

## Price Elasticity Outputs

### 2. Elasticity Summary Table
**File**: `reports/tables/elasticity_summary.csv`

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| `product_name` | Product name or UPC | "Coca-Cola 2L" |
| `category` | Product category | "Beverages" |
| `elasticity` | Price elasticity coefficient | -1.45 |
| `std_error` | Standard error of estimate | 0.12 |
| `p_value` | Statistical significance | 0.001 |
| `confidence_interval_lower` | Lower bound (95% CI) | -1.68 |
| `confidence_interval_upper` | Upper bound (95% CI) | -1.22 |
| `elasticity_category` | Classification | "Elastic" |
| `r_squared` | Model fit | 0.62 |
| `sample_size` | Number of observations | 523 |

**Sample Rows**:
```
product_name,category,elasticity,std_error,p_value,elasticity_category
Coca-Cola 2L,Beverages,-1.45,0.12,0.001,Elastic
Whole Milk 1 Gal,Dairy,-0.52,0.08,0.032,Inelastic
Wonder Bread,Bakery,-0.89,0.15,0.018,Inelastic
Oreo Cookies,Snacks,-1.78,0.21,0.000,Highly Elastic
```

### 3. Elasticity by Category Chart
**File**: `reports/figures/elasticity_by_category.png`

**Type**: Horizontal bar chart

**Visualization**:
```
Category             Elasticity
─────────────────────────────────
Beverages        |████████████ -1.8
Snacks           |██████████ -1.5
Bakery           |███████ -1.1
Personal Care    |████ -0.7
Dairy            |██ -0.5
                 -2.0  -1.0   0
```

**Design Notes**:
- Bars colored by elasticity (red = elastic, green = inelastic)
- Error bars showing 95% confidence intervals
- Reference line at |ε| = 1.0 (unit elastic threshold)

### 4. Demand Curves (Top 5 Products)
**File**: `reports/figures/demand_curves.png`

**Type**: Scatter plot with fitted regression line

**Axes**:
- X-axis: log(Price)
- Y-axis: log(Quantity)

**Elements**:
- Scatter points: Actual observations
- Line: Fitted demand curve (slope = elasticity)
- Annotation: Elasticity value and R²

**Example** (for Coca-Cola):
```
log(Quantity)
     |    ●
   4 |  ●   ● 
     | ●  ●   ●
   3 |●     ●
     |   ε = -1.45
   2 |   R² = 0.62
     |________________
       1.0   1.5   log(Price)
```

### 5. Elasticity Distribution Histogram
**File**: `reports/figures/elasticity_distribution.png`

**Type**: Histogram

**Bins**: 0.2 increments (e.g., -2.0 to -1.8, -1.8 to -1.6, ...)

**Design Notes**:
- Vertical reference lines at |ε| = 0.5, 1.0, 1.5
- Color zones: Inelastic (blue), Unit elastic (yellow), Elastic (red)

---

## Promotional ROI Outputs

### 6. Promotional ROI Summary Table
**File**: `reports/tables/promo_roi_summary.csv`

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| `product_name` | Product name | "Coca-Cola 2L" |
| `promotion_type` | Type of promotion | "BOGO 50% Off" |
| `total_promo_cost` | Total discount amount ($) | 5,240 |
| `incremental_units` | Additional units sold | 1,850 |
| `incremental_revenue` | Additional revenue ($) | 7,390 |
| `incremental_profit` | Additional profit ($) | 2,217 (30% margin) |
| `roi_pct` | ROI percentage | 42.3% |
| `num_promo_events` | Number of promotional weeks | 8 |

**Sample Rows**:
```
product_name,promotion_type,total_promo_cost,incremental_profit,roi_pct
Coca-Cola 2L,BOGO 50% Off,5240,2217,42.3
Milk 1 Gal,Coupon $1 Off,3100,-450,-14.5
Oreo Cookies,25% Off,2890,1340,46.4
```

### 7. ROI by Promotion Type Chart
**File**: `reports/figures/roi_by_promotion_type.png`

**Type**: Bar chart

**Visualization**:
```
Promotion Type         ROI
────────────────────────────
BOGO               █████████ 85%
Tiered Discount    ██████ 52%
Loyalty Reward     ████ 38%
Coupon             ██ 19%
% Off              █ 12%
Manager Discount   [-15%]
                   0%  50%  100%
```

**Design Notes**:
- Bars colored by ROI tier (green = high, yellow = moderate, red = negative)
- Reference line at 0% ROI
- Annotate each bar with exact ROI percentage

### 8. ROI Waterfall Chart
**File**: `reports/figures/roi_waterfall.png`

**Type**: Waterfall chart

**Components**:
1. Baseline sales (starting point)
2. + Incremental units
3. × Average promotional price → Incremental revenue
4. - Promotional cost
5. × Margin → Incremental profit
6. Final ROI

**Example**:
```
$10K |       +$7.4K
     |    ╔════════╗
 $5K |    ║        ║  -$5.2K
     |    ║  ╔═══╗ ║═════╗
 $0  |════╝  ║   ╚═╝     ║  +$2.2K
     |       ║            ╚══╗
-$5K |       ╚═══════════════╝
         Base  Inc.   Cost  Profit
              Rev
```

### 9. High vs. Low ROI Products
**File**: `reports/figures/roi_segments.png`

**Type**: Quadrant scatter plot

**Axes**:
- X-axis: Price elasticity (|ε|)
- Y-axis: ROI (%)

**Quadrants**:
- **Top-Left** (Inelastic + High ROI): Ideal for price increases
- **Top-Right** (Elastic + High ROI): Scale promotions
- **Bottom-Left** (Inelastic + Low ROI): Reduce promotions
- **Bottom-Right** (Elastic + Low ROI): Risky, consider discontinuation

### 10. ROI Time Series
**File**: `reports/figures/roi_over_time.png`

**Type**: Line chart

**Axes**:
- X-axis: Month
- Y-axis: Average ROI (%)

**Elements**:
- Line: Monthly average ROI
- Shaded area: Holiday periods (higher ROI expected)
- Reference line: Portfolio-wide average ROI

---

## Strategic Recommendations

### 11. Pricing Recommendation Table
**File**: `reports/tables/pricing_recommendations.csv`

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| `product_name` | Product name | "Whole Milk 1 Gal" |
| `current_price` | Current average price | $4.49 |
| `elasticity` | Price elasticity | -0.52 |
| `recommendation` | Action | "Increase price 5%" |
| `new_price` | Recommended price | $4.71 |
| `revenue_impact` | Projected revenue change | +$12,400/year |
| `confidence` | Confidence level | "High" |

**Sample Rows**:
```
product_name,current_price,elasticity,recommendation,new_price,revenue_impact
Whole Milk,$4.49,-0.52,Increase 5%,$4.71,+$12400
Coca-Cola,$3.99,-1.45,Hold price,$3.99,$0
Oreo Cookies,$5.49,-1.78,Avoid increases,$5.49,$0
```

### 12. Promotional Optimization Table
**File**: `reports/tables/promotional_recommendations.csv`

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| `product_name` | Product name | "Coca-Cola 2L" |
| `current_promo_freq` | Current # of promos/year | 12 |
| `current_avg_roi` | Current ROI | 42% |
| `recommendation` | Action | "Increase frequency to 18" |
| `expected_roi` | Expected ROI after change | 45% |
| `incremental_profit` | Additional profit/year | +$3,200 |

### 13. High-Impact Opportunities Chart
**File**: `reports/figures/high_impact_opportunities.png`

**Type**: Bubble chart

**Axes**:
- X-axis: ROI (%)
- Y-axis: Incremental profit ($)

**Bubble Size**: Frequency of promotion (larger = more frequent)

**Interpretation**:
- Large bubbles in top-right = high-priority opportunities (scale these)
- Bubbles in bottom-left = low-value promotions (eliminate these)

---

## Technical Appendix

### 14. Regression Results Table
**File**: `reports/tables/regression_results.csv`

**Content**: Full regression output for all products

**Columns**:
- Coefficient estimates (intercept, log_price, promo, controls)
- Standard errors
- t-statistics
- p-values
- R², Adjusted R², AIC, BIC

### 15. Model Diagnostics
**File**: `reports/figures/diagnostics/`

**Charts** (per product or category):
- **Residuals vs. Fitted**: Check for heteroscedasticity
- **Q-Q Plot**: Check normality of residuals
- **ACF Plot**: Check for autocorrelation
- **Actual vs. Predicted**: Validate model predictions

### 16. Data Quality Report
**File**: `reports/data_quality_report.md`

**Content**:
- Sample size by product/category
- Missing data percentage
- Outliers detected and removed
- Price variation statistics (min, max, std dev)
- Promotional coverage (% of transactions with promos)

---

## Deliverable Checklist

### For Business Stakeholders
- [x] Executive summary (1-page PDF)
- [x] Elasticity summary table (CSV)
- [x] ROI summary table (CSV)
- [x] Pricing recommendations (CSV)
- [x] Promotional recommendations (CSV)
- [x] Key charts (PNG/PDF):
  - Elasticity by category
  - ROI by promotion type
  - High-impact opportunities
  - ROI waterfall

### For Technical Audience
- [x] Full regression results (CSV)
- [x] Model diagnostics (PNG)
- [x] Data quality report (MD)
- [x] Demand curves for top products (PNG)
- [x] Elasticity distribution (PNG)

### For Presentations
- [x] PowerPoint deck with:
  - Executive summary slide
  - Key findings (2-3 slides)
  - Recommendations (2-3 slides)
  - Appendix with technical details

---

## File Naming Conventions

**Tables**: `{metric}_{aggregation}.csv`
- Example: `elasticity_by_product.csv`, `roi_by_promotion_type.csv`

**Figures**: `{metric}_{chart_type}.png`
- Example: `elasticity_histogram.png`, `roi_waterfall.png`

**Reports**: `{report_name}_{version}.{format}`
- Example: `executive_summary_v1.0.pdf`, `technical_report_v1.0.md`

---

## Visualization Style Guide

### Color Palette
- **Primary**: Blues (#1f77b4, #aec7e8) for general charts
- **Elasticity**:
  - Inelastic: Green (#2ca02c)
  - Elastic: Orange (#ff7f0e)
  - Highly Elastic: Red (#d62728)
- **ROI**:
  - High (>50%): Dark Green (#2ca02c)
  - Positive (0-50%): Light Green (#98df8a)
  - Negative (<0%): Red (#d62728)

### Chart Specifications
- **Font**: Sans-serif (Arial, Helvetica)
- **Title**: 16pt bold
- **Axis labels**: 12pt
- **Gridlines**: Light gray, dashed
- **DPI**: 300 for print, 150 for web

### Accessibility
- Use colorblind-friendly palette
- Include data labels on bars/points
- Provide alt text for all charts

---

**Document Version**: 1.0  
**Last Updated**: 2023-12-21  
**Author**: Analytics Team
