# SKU Inventory Data Integration Portfolio Project

This repository contains a public, anonymized version of a SKU-level data integration workflow built for supplier feed reconciliation, ecommerce catalog alignment, and operational data quality controls. The project demonstrates how supplier inventory feeds and catalog data can be ingested, standardized, merged, validated, and converted into business-ready analytics outputs.

The original engagement used private operational feeds. In this portfolio version, all source systems, credentials, paths, supplier names, and sensitive product data have been replaced with safe demo inputs while preserving the same technical patterns.

## Project Contents

| File | Purpose |
|---|---|
| `merge_sku_updated.ipynb` | Client-facing exploratory notebook showing the end-to-end data reading, merge, quality control, and analytics workflow |
| `hourly_sku_data_update_demo.py` | Production-style demo script intended to run hourly on a Windows server through Task Scheduler |

## Business Context

The business objective is to create a dependable SKU-level inventory view by reconciling:

- Supplier inventory and pricing feeds
- Secondary supplier stock and SKU identifiers
- Ecommerce catalog records from an API or catalog export

The resulting dataset supports:

- Ecommerce availability decisions
- Catalog mapping remediation
- Supplier price and stock discrepancy review
- Inventory value estimation
- Operational prioritization for data and category teams

## Technical Approach

The workflow follows a practical data integration pattern:

1. Read heterogeneous source formats: semicolon CSV, pipe-delimited TXT, and catalog API/XML-style records.
2. Detect encodings and standardize source-specific schemas.
3. Normalize product identifiers before joining.
4. Validate duplicate keys and invalid commercial values before merge.
5. Reconcile supplier feeds using conservative ecommerce rules:
   - use the higher available price when supplier prices disagree
   - use the lower available quantity when stock counts disagree
6. Outer-join the reconciled supplier view with the catalog to expose source coverage gaps.
7. Create business analytics columns for availability, catalog alignment, inventory value, and review priority.

## Key Output Columns

| Column | Description |
|---|---|
| `selected_unit_price` | Price selected after applying the supplier reconciliation rule |
| `sellable_qty` | Quantity available for ecommerce after applying the lower-stock rule |
| `source_coverage` | Whether the SKU appears in supplier data, catalog data, or both |
| `availability_status` | In-stock, low-stock, or out-of-stock classification |
| `catalog_alignment_status` | Matched, missing from catalog, or missing from supplier feeds |
| `sellable_inventory_value` | Estimated value of sellable inventory |
| `price_gap_pct` | Relative price variance between supplier feeds |
| `stock_gap` | Inventory quantity difference between supplier feeds |
| `review_priority` | Rule-based triage category for operational follow-up |


```

## Hourly Demo Script

`hourly_sku_data_update_demo.py` is a production-style demo intended for a Windows server. It is designed to be run hourly as a one-shot task, which is easier to monitor and recover than a permanently running Python process.

Recommended Windows Task Scheduler command:

```powershell
py -3 C:\path\to\hourly_sku_data_update_demo.py --run-once
```

The script also supports local/demo looping:

```bash
python hourly_sku_data_update_demo.py --loop-hourly
```

For testing, force a rebuild even if sources have not changed:

```bash
python hourly_sku_data_update_demo.py --run-once --force
```

## Configuration

The script is configured through environment variables so source paths and credentials do not need to be stored in code.

| Environment variable | Purpose | Example |
|---|---|---|
| `SKU_SYNC_BASE_DIR` | Base working directory | `C:\sku_sync_demo` |
| `SKU_SOURCE_A_PATH` | Path to supplier CSV feed | `C:\data\source_a_inventory.csv` |
| `SKU_SOURCE_B_PATH` | Path to supplier TXT feed | `C:\data\source_b_inventory.txt` |
| `SKU_CATALOG_API_URL` | Catalog API endpoint | `https://api.example.com/catalog/products` |
| `SKU_CATALOG_API_TOKEN` | API bearer token | stored securely outside code |
| `SKU_DEMO_MODE` | Generate anonymized demo inputs when set to `1` | `1` for demo, `0` for production |
| `SKU_API_TIMEOUT_SECONDS` | API timeout | `30` |
| `SKU_API_RETRIES` | API retry count | `3` |


```

## Runtime Outputs

When the hourly script runs, it creates the following folders under `SKU_SYNC_BASE_DIR`:

| Folder | Contents |
|---|---|
| `raw` | Demo input files and optional API response snapshots |
| `output` | Latest integrated SKU inventory CSV |
| `state` | Last successful run metadata and source fingerprints |
| `logs` | Rotating execution logs |

The main output file is:

```text
output/sku_inventory_latest.csv
```

## Change Detection

The hourly script avoids unnecessary rebuilds by storing source fingerprints from the last successful run:

- local file size, modified timestamp, and SHA-256 hash
- stable hash of the catalog API payload

If the source snapshot has not changed, the script logs that the output is already current and exits successfully.

## Data Quality Controls

The pipeline checks for:

- duplicate product IDs before merge
- missing or malformed API fields
- negative quantity values
- negative price values
- unexpected API response shape

These checks are intentionally strict. A failed source should not overwrite the last known-good output.

## Dependencies

The project uses:

```text
pandas
numpy
chardet
jupyter
```


## Notes on Anonymization

This repository is designed for public review. The included notebook and hourly demo script use anonymized source names, generic API placeholders, and synthetic product records.
It does not publish private source files, credentials, real endpoint URLs, client-specific documentation, or raw operational exports alongside these files.


