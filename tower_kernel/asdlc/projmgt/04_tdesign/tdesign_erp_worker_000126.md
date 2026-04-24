# Technical Design: ERP Ingestion Worker Engine
**ID**: `tdesign_erp_worker_000126`
**Status**: DRAFT
**Requirement Reference**: `fdesign_erp_ingestion_000125`

## 1. Class Structure: `ERPIngestionWorker`

Located in `src/tower_kernel/ingest/erp_worker.py`.

### Attributes
- `source_path`: Root directory of ERP CSV dump.
- `output_path`: Root directory for Parquet lake.
- `schemas`: Dictionary of `pl.Schema` objects for each table.

### Methods
- `ingest_all()`: Orchestrates the loading and saving of all 4 tables.
- `load_table(expected_type: str) -> pl.DataFrame`:
    - Loads the CSV with strict schema enforcement.
    - Injects audit columns (`ingestion_timestamp`).
- `transform_transactions(tx_df: pl.DataFrame, terms_df: pl.DataFrame) -> pl.DataFrame`:
    - Joins transactions and terms to verify integrity.
- `save_parquet(df: pl.DataFrame, table_name: str, partition_by: list[str])`:
    - Writes the DataFrame to the partitioned Parquet store.

## 2. Ingestion Schema (Sample)

```python
{
    "Seller": pl.Schema({
        "seller_company_id_ferc": pl.String,
        "seller_company_name": pl.String,
    }),
    "Transaction": pl.Schema({
        "transaction_unique_id": pl.String,
        "term_id": pl.String,
        "transaction_begin_date": pl.Datetime,
        "transaction_quantity": pl.Float64,
        "total_transaction_charge": pl.Float64,
    })
}
```

## 3. High-Performance Optimizations
- **Streaming Scans**: Use `pl.scan_csv` where possible.
- **Batched Write**: `write_parquet` with `use_pyarrow=True` for partitioned output.
