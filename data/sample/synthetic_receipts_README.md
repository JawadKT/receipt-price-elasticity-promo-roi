# Synthetic Receipt Data

This directory contains synthetic (fake) receipt data designed to mirror the real schema while containing no sensitive or proprietary information.

---

## Purpose

The synthetic dataset allows:
1. **Testing**: Validate data processing scripts without accessing real data
2. **Development**: Build and debug analysis pipelines locally
3. **Documentation**: Demonstrate expected data format and structure
4. **Onboarding**: Help new team members understand the data model
5. **Reproducibility**: Share code with external collaborators safely

---

## Files

### `synthetic_receipts.csv`
**Status**: ⚠️ To be generated

**Description**: Sample receipt line-item transactions

**Schema**: See `docs/data_dictionary.md`

**Specifications**:
- **Rows**: 10,000 synthetic transactions
- **Products**: 50 fake products across 5 categories
- **Stores**: 10 fictional store locations
- **Time Period**: 12 months (Jan 2023 - Dec 2023)
- **Promotions**: ~20% of transactions include promotions

---

## Data Generation Method

### Approach
Use Python's `Faker` library and custom logic to create realistic but synthetic data.

### Generation Script
**Location**: `src/data/generate_synthetic_data.py` (to be created)

**Pseudocode**:
```python
import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
Faker.seed(42)  # For reproducibility
np.random.seed(42)

# Define products
products = [
    {'upc': f'{1234567890 + i:012d}', 
     'name': fake.word().title() + ' ' + fake.word().title(),
     'category': np.random.choice(['Beverages', 'Snacks', 'Dairy', 'Bakery', 'Personal Care']),
     'base_price': np.random.uniform(1.99, 15.99)}
    for i in range(50)
]

# Generate transactions
transactions = []
for i in range(10000):
    txn_id = f"TXN_{fake.date_between(start_date='-1y', end_date='today').strftime('%Y%m%d')}_{i:06d}"
    store_id = f"STORE_{np.random.randint(1, 11):04d}"
    
    # Select random product
    product = np.random.choice(products)
    
    # Generate quantity
    quantity = np.random.choice([1, 1, 1, 2, 2, 3], p=[0.5, 0.2, 0.1, 0.1, 0.05, 0.05])
    
    # Determine if promotion
    is_promo = np.random.random() < 0.20
    
    # Calculate price
    base_price = product['base_price']
    if is_promo:
        discount_pct = np.random.choice([10, 15, 20, 25, 50])
        final_price = base_price * (1 - discount_pct / 100)
        promotion_type = np.random.choice(['Percent Off', 'BOGO', 'Coupon', 'Loyalty'])
    else:
        final_price = base_price
        promotion_type = None
    
    transactions.append({
        'transaction_id': txn_id,
        'line_item_id': 1,
        'transaction_date': fake.date_between(start_date='-1y', end_date='today'),
        'store_id': store_id,
        'upc': product['upc'],
        'product_name': product['name'],
        'category': product['category'],
        'quantity': quantity,
        'unit_price': base_price,
        'discount_amount': (base_price - final_price) * quantity if is_promo else 0,
        'final_price': final_price,
        'is_promotion': is_promo,
        'promotion_type': promotion_type
    })

# Save to CSV
df = pd.DataFrame(transactions)
df.to_csv('data/sample/synthetic_receipts.csv', index=False)
```

---

## Data Characteristics

### Products
- **UPCs**: Sequential 12-digit codes starting from 001234567890
- **Names**: Randomly generated (e.g., "Happy Snack", "Green Beverage")
- **Categories**: 5 categories with ~10 products each
- **Price Range**: $1.99 - $15.99

### Stores
- **Store IDs**: STORE_0001 through STORE_0010
- **No geographic data**: Avoids any real location identifiers

### Pricing
- **Base Prices**: Fixed per product (with small random variation)
- **Promotions**: 20% of transactions have discounts
- **Discount Depths**: 10%, 15%, 20%, 25%, or 50% off

### Temporal Patterns
- **Date Range**: Full 12 months
- **Seasonality**: No explicit seasonality (can be added if needed)
- **Day-of-Week**: Uniform distribution (can be adjusted for realism)

---

## Differences from Real Data

### What's Included
✅ Correct schema and data types  
✅ Realistic price ranges  
✅ Promotion flags and discount amounts  
✅ Multi-product, multi-store structure  
✅ Sufficient volume for testing (10K rows)

### What's Missing
❌ Real product names and brands  
❌ Actual store locations  
❌ Real customer behavior patterns  
❌ True seasonality and trends  
❌ Competitive dynamics  
❌ Regional pricing variations  
❌ Returns and refunds  

### Privacy & Security
- **No PII**: No customer IDs or personal information
- **No sensitive data**: All values are fabricated
- **No proprietary info**: No real product names, prices, or sales figures
- **Safe to share**: Can be committed to public repositories

---

## Validation

Before using synthetic data, validate that:
1. Schema matches `docs/data_dictionary.md`
2. All required fields are non-null
3. Data types are correct (dates as dates, numbers as numbers)
4. Price logic is consistent (final_price = unit_price - discount)
5. Sufficient variation for testing (multiple products, stores, dates)

### Validation Script
```bash
# Run data validation
python src/data/validate_data.py --file data/sample/synthetic_receipts.csv
```

---

## Usage Examples

### Load and Explore
```python
import pandas as pd

# Load synthetic data
df = pd.read_csv('data/sample/synthetic_receipts.csv', parse_dates=['transaction_date'])

# Basic stats
print(df.shape)
print(df.info())
print(df.describe())

# Check promotion distribution
print(df['is_promotion'].value_counts())
```

### Test Elasticity Pipeline
```bash
# Run elasticity estimation on synthetic data
python src/models/elasticity_log_log.py --input data/sample/synthetic_receipts.csv
```

---

## Generating New Synthetic Data

To regenerate or create additional synthetic datasets:

```bash
# Generate synthetic data
python src/data/generate_synthetic_data.py --rows 10000 --output data/sample/synthetic_receipts.csv

# Generate with specific seed (for reproducibility)
python src/data/generate_synthetic_data.py --rows 10000 --seed 42 --output data/sample/synthetic_receipts_v2.csv
```

---

## Future Enhancements

### Potential Improvements
1. **Realistic Patterns**:
   - Add day-of-week effects (higher sales on weekends)
   - Add seasonality (holiday spikes)
   - Add product affinity (basket composition)

2. **Complex Scenarios**:
   - Include returns and refunds
   - Add bundle pricing (Buy 2 Get 1 Free)
   - Simulate stockpiling behavior

3. **Data Quality Issues**:
   - Introduce intentional missing values
   - Add outliers and data entry errors
   - Include duplicate transactions

4. **Volume**:
   - Generate larger datasets (100K+ rows) for performance testing
   - Create multi-year time series

---

## License

This synthetic data is provided for educational and development purposes only. It contains no real information and can be freely used, modified, and distributed.

---

## Contact

For questions about synthetic data generation or to request specific test scenarios, please open an issue in this repository.

---

**Document Version**: 1.0  
**Last Updated**: 2023-12-21  
**Status**: Placeholder - data file to be generated
