# Data Dictionary: Receipt Line-Item Dataset

This document describes the schema for transaction-level receipt data used in price elasticity and promotional ROI analysis.

---

## Dataset Overview

- **Granularity**: One row per product purchased per transaction (line-item level)
- **Time Period**: Typically 12-24 months of historical data
- **Update Frequency**: Daily or weekly batch loads
- **Primary Key**: `transaction_id` + `line_item_id`

---

## Column Definitions

### Transaction Identifiers

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `transaction_id` | STRING | Unique identifier for the transaction/receipt | "TXN_20231215_000123" | • Duplicates due to data pipeline errors<br>• Non-unique IDs across stores/dates<br>• Missing values (rare) |
| `line_item_id` | INTEGER | Sequential line number within a transaction | 1, 2, 3, ... | • Non-sequential numbering<br>• Gaps in sequence (deleted items)<br>• Null values |
| `receipt_number` | STRING | Human-readable receipt number printed on physical receipt | "R-45678", "00123456" | • Not unique across stores<br>• Format inconsistencies<br>• May be reused over time |

### Temporal Fields

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `transaction_timestamp` | TIMESTAMP | Date and time of transaction completion | "2023-12-15 14:32:17" | • Timezone inconsistencies<br>• Batch uploads timestamped incorrectly<br>• Future dates (clock errors)<br>• Missing time component |
| `transaction_date` | DATE | Date of transaction (derived from timestamp) | "2023-12-15" | • Misalignment with timestamp<br>• Batch processing dates vs. actual transaction dates |
| `day_of_week` | STRING/INTEGER | Day of week (1=Monday, 7=Sunday or Mon/Tue/...) | "Friday", 5 | • Inconsistent encoding (text vs. numeric)<br>• Incorrect calculation from date |
| `week_of_year` | INTEGER | ISO week number (1-53) | 50 | • Wrong year boundary handling<br>• Non-ISO standards (week starting Sunday vs. Monday) |
| `month` | INTEGER | Month (1-12) | 12 | • Zero-indexed months (0-11)<br>• String values ("December") |
| `year` | INTEGER | Four-digit year | 2023 | • Two-digit years ("23")<br>• Rare but possible: incorrect century |

### Location Information

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `store_id` | STRING | Unique identifier for the retail store/location | "STORE_1234", "NYC_001" | • Changed over time (store renovations, ownership changes)<br>• Non-standardized formats<br>• Temporary stores with duplicate IDs |
| `store_name` | STRING | Human-readable store name | "Springfield Mall", "Downtown Store" | • Name changes not reflected<br>• Typos and spelling variations<br>• Excessive whitespace |
| `store_format` | STRING | Store type/format classification | "Supermarket", "Convenience", "Hypermarket" | • Inconsistent categorization<br>• Missing values<br>• Format changes over time |
| `region` | STRING | Geographic region or market | "Northeast", "CA-Bay Area" | • Inconsistent granularity (state vs. region)<br>• Null for online orders |
| `zip_code` | STRING | Postal code of store location | "02134", "90210" | • Leading zeros dropped (numeric storage)<br>• ZIP+4 vs. 5-digit inconsistencies<br>• International formats |

### Product Information

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `upc` | STRING | Universal Product Code (barcode) | "012345678905", "00000012345678" | • Leading zeros dropped<br>• Mixed UPC-A (12-digit) and UPC-E (8-digit)<br>• Checksum digit errors<br>• Store-specific "dummy" UPCs for bulk items |
| `product_id` | STRING | Internal product identifier (may differ from UPC) | "PROD_98765" | • Multiple IDs for same product (data integration issues)<br>• Null values for ad-hoc items |
| `product_name` | STRING | Product description as appears on receipt | "Coca-Cola 2L Bottle", "Organic Bananas" | • Truncation (character limits)<br>• Inconsistent formatting (abbreviations, case)<br>• Special characters and encoding issues |
| `brand` | STRING | Product brand name | "Coca-Cola", "Dole", "Store Brand" | • Misspellings<br>• "Generic" vs. "Store Brand" inconsistencies<br>• Missing for private label |
| `category` | STRING | Product category (department level) | "Beverages", "Produce", "Dairy" | • Inconsistent taxonomy over time<br>• Multiple classification schemes<br>• Miscategorized products |
| `subcategory` | STRING | Product subcategory (finer grain) | "Soft Drinks", "Fresh Fruit", "Milk" | • Sparse/missing subcategories<br>• Overlapping definitions |
| `department` | STRING | High-level department grouping | "Grocery", "Fresh", "Non-Food" | • Null values<br>• Changes in organizational structure |
| `package_size` | STRING | Package size/unit of measure | "2L", "1 lb", "12 oz" | • Inconsistent units (oz vs. ml, lb vs. kg)<br>• Free text entry (hard to parse)<br>• Missing for variable-weight items |

### Pricing & Quantity

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `quantity` | DECIMAL | Number of units purchased | 1.0, 2.5, 0.75 | • Negative quantities (returns not flagged)<br>• Zero quantities (voided items)<br>• Extreme outliers (data entry errors)<br>• Fractional quantities for non-weight items |
| `unit_price` | DECIMAL | Price per unit (before discounts) | 3.99, 12.50 | • Includes discount (not "regular" price)<br>• Null for promotional bundles<br>• Currency formatting (strings like "$3.99")<br>• Negative prices (incorrectly coded returns) |
| `regular_price` | DECIMAL | Regular/full price without any promotions | 4.99, 15.00 | • Often missing or unreliable<br>• Not updated for permanent price changes<br>• May reflect "fake" MSRPs |
| `discount_amount` | DECIMAL | Total discount applied to this line item | 1.00, 0.00 | • Negative values (sign convention errors)<br>• Missing when promotions are active<br>• Double-counting (loyalty + coupon) |
| `final_price` | DECIMAL | Actual price paid per unit (after all discounts) | 2.99, 12.50 | • Calculation errors (unit_price - discount ≠ final_price)<br>• Includes tax (should be pre-tax) |
| `line_total` | DECIMAL | Total amount for this line (quantity × final_price) | 5.98, 25.00 | • Rounding discrepancies<br>• Includes tax when should be pre-tax<br>• Negative for returns |
| `tax_amount` | DECIMAL | Sales tax applied to this line item | 0.52, 0.00 | • Missing or zero for taxable items<br>• Incorrect tax rates<br>• Mixed in with line_total |

### Promotional Flags

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `is_promotion` | BOOLEAN | Whether any promotion was applied | TRUE, FALSE, 1, 0 | • False positives (price changes treated as promos)<br>• False negatives (promotions not flagged)<br>• Mixed encoding (1/0, T/F, Y/N) |
| `promotion_type` | STRING | Type of promotion applied | "Percentage Off", "BOGO", "Coupon", "Loyalty Discount" | • Null when is_promotion = TRUE<br>• Multiple promotions concatenated<br>• Non-standardized labels ("10% off" vs. "Percent Discount") |
| `promotion_id` | STRING | Unique identifier for the promotional campaign | "PROMO_SUMMER2023_001" | • Missing for ad-hoc manager discounts<br>• Not unique across regions/stores |
| `coupon_code` | STRING | Coupon or promo code entered | "SAVE10", "LOYALTY20" | • Null for non-coupon promotions<br>• Case sensitivity issues |
| `loyalty_discount` | BOOLEAN | Whether loyalty program discount was applied | TRUE, FALSE | • Overlap with other promotion flags<br>• Missing values |
| `discount_percentage` | DECIMAL | Percentage discount (if applicable) | 10.0, 25.0, 50.0 | • Stored as decimals (0.1 vs. 10)<br>• Missing for dollar-off promotions<br>• Calculated incorrectly |

### Cost & Margin (Optional - May Not Be Available)

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `cost_of_goods_sold` | DECIMAL | COGS per unit | 2.50, 8.00 | • Highly sensitive, often unavailable<br>• Outdated costs (not current)<br>• Missing for third-party vendors |
| `gross_margin` | DECIMAL | Gross profit margin (revenue - COGS) / revenue | 0.35, 0.42 | • Calculated on discounted vs. regular price inconsistencies<br>• Negative margins (clearance items) |

### Customer Information (If Available via Loyalty Program)

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `customer_id` | STRING | Unique identifier for loyalty program member | "CUST_567890", "ANON" | • Null for non-members (majority of transactions)<br>• Household vs. individual ID confusion<br>• Privacy concerns (anonymization needed) |
| `customer_segment` | STRING | Customer segment/tier | "Platinum", "Gold", "Regular" | • Inconsistent segmentation logic<br>• Temporal changes not tracked |

### Return/Refund Flags

| Column Name | Data Type | Description | Example Values | Common Data Quality Issues |
|------------|-----------|-------------|----------------|---------------------------|
| `is_return` | BOOLEAN | Whether this line item is a return/refund | TRUE, FALSE | • Returns not flagged (negative quantities instead)<br>• Exchanges coded as returns |
| `original_transaction_id` | STRING | Transaction ID of original purchase (for returns) | "TXN_20231210_000098" | • Null for most returns<br>• Invalid references (original txn not in data) |

---

## Data Quality Rules & Validation Checks

### Critical Validations
1. **Primary Key Uniqueness**: `transaction_id` + `line_item_id` must be unique
2. **Non-Null Constraints**: `transaction_id`, `transaction_date`, `upc`, `quantity`, `final_price` must not be null
3. **Referential Integrity**: `store_id` should exist in store master table; `upc` should exist in product master
4. **Logical Consistency**:
   - `quantity > 0` (or flag returns separately)
   - `final_price >= 0` (unless explicitly a return)
   - `line_total = quantity × final_price` (within rounding tolerance)
   - If `is_promotion = TRUE`, then `discount_amount > 0`
   - `transaction_date <= current_date` (no future dates)

### Common Data Quality Issues Summary

#### High Severity
- **Missing transaction IDs**: Cannot join or aggregate data
- **Incorrect prices**: Undermines all financial calculations
- **Untagged promotions**: Biases elasticity estimates
- **Duplicate records**: Double-counts sales and revenue

#### Medium Severity
- **Missing UPCs**: Requires fuzzy matching on product names
- **Inconsistent categorization**: Complicates category-level analysis
- **Null regular_price**: Difficult to calculate discount depth
- **Timezone issues**: Affects daily aggregation and trend analysis

#### Low Severity
- **Missing store names**: Can use store_id instead
- **Truncated product names**: Annoying but not critical
- **Formatting inconsistencies**: Fixable with standardization scripts

---

## Recommended Preprocessing Steps

1. **Standardize Data Types**: Convert strings to appropriate numeric/date types; handle mixed formats
2. **Deduplicate**: Remove exact duplicate rows; investigate near-duplicates
3. **Flag Returns**: Create explicit `is_return` flag from negative quantities or return indicators
4. **Impute Missing Values**: 
   - Fill missing `regular_price` with median price for that product
   - Infer `is_promotion` from discount_amount > 0
5. **Outlier Detection**: Flag transactions with extreme quantities, prices, or discounts for manual review
6. **Derive Features**:
   - Calculate `discount_percentage = (regular_price - final_price) / regular_price`
   - Create `price_per_unit` for variable-weight items
   - Add calendar features: `is_weekend`, `is_holiday`, `season`
7. **Aggregate**: Roll up to product-day or product-week level for time-series modeling

---

## Example Data Snippet

```csv
transaction_id,line_item_id,transaction_date,store_id,upc,product_name,quantity,unit_price,discount_amount,final_price,is_promotion,promotion_type
TXN_20231215_001,1,2023-12-15,STORE_1234,012345678905,Coca-Cola 2L,2,3.99,1.00,2.99,TRUE,BOGO 50% Off
TXN_20231215_001,2,2023-12-15,STORE_1234,098765432109,Bananas (per lb),1.5,0.59,0.00,0.59,FALSE,
TXN_20231215_002,1,2023-12-15,STORE_1234,111222333444,Milk 1 Gallon,1,4.49,0.50,3.99,TRUE,Coupon
```

---

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2023-12-21 | 1.0 | Initial data dictionary created |

---

## Contact

For questions about data schema or quality issues, contact the Data Engineering team or open an issue in this repository.
