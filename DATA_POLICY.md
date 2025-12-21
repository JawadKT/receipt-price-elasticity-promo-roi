# Data Policy

This repository is designed to be safe to share publicly by separating
**real receipts** from **synthetic or anonymized data**.

## Directives

- **Real receipt data must never be committed to git.**
  - Place any raw, identifiable transaction data under `data/raw/`.
  - `data/raw/` is (and should remain) gitignored.
- **Synthetic or anonymized examples go in `data/sample/`.**
  - The sample files in this repository (e.g.
    `data/sample/synthetic_receipts.csv`) contain only synthetic data.
- **Intermediate and processed data for real projects** should live under
  `data/interim/` and `data/processed/` and should only be committed if
  they are fully anonymized and approved for sharing.
- **Reports in `reports/` are generally safe to commit** as long as they do
  not include customer identifiers or other sensitive columns.

If you adapt this project to real receipts, review your organization’s
privacy and data-governance policies before sharing outputs externally.