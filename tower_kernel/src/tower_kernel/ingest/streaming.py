import zipfile
import io
import shutil
import tempfile
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import os
from pathlib import Path
from typing import Optional

def stream_filing_to_polars(master_zip_path: str, sub_zip_name: str) -> dict[str, pl.DataFrame]:
    """
    Extracts transaction and identity CSVs from a nested company zip.
    Returns a dictionary of Polars DataFrames.
    """
    results = {}
    with zipfile.ZipFile(master_zip_path, 'r') as master:
        try:
            with master.open(sub_zip_name) as sub_file_stream:
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_sub:
                    shutil.copyfileobj(sub_file_stream, tmp_sub)
                    tmp_sub_path = tmp_sub.name
            
            try:
                with zipfile.ZipFile(tmp_sub_path) as sub_zip:
                    # 1. Transactions Capture
                    tx_file = next((f for f in sub_zip.namelist() if '_transactions.csv' in f.lower()), None)
                    if tx_file:
                        results['transactions'] = _ingest_csv(sub_zip, tx_file, "transactions")
                    
                    # 2. Identity Capture
                    id_file = next((f for f in sub_zip.namelist() if '_ident.csv' in f.lower() or '_identity.csv' in f.lower()), None)
                    if id_file:
                        results['identity'] = _ingest_csv(sub_zip, id_file, "identity")
                        
                    return results
            finally:
                if os.path.exists(tmp_sub_path):
                    os.remove(tmp_sub_path)
        except Exception as e:
            print(f"Error streaming {sub_zip_name}: {e}")
            return {}

def _ingest_csv(sub_zip: zipfile.ZipFile, filename: str, table_type: str) -> Optional[pl.DataFrame]:
    """Internal helper to ingest a specific CSV within a company sub-zip."""
    with sub_zip.open(filename) as csv_stream:
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
            shutil.copyfileobj(csv_stream, tmp_csv)
            tmp_csv_path = tmp_csv.name
        
        try:
            if table_type == "transactions":
                raw_dtypes = {
                    "transaction_unique_id": pl.Utf8,
                    "transaction_unique_identifier": pl.Utf8,
                    "seller_company_name": pl.Utf8,
                    "customer_company_name": pl.Utf8,
                    "ferc_tariff_reference": pl.Utf8,
                    "contract_service_agreement": pl.Utf8,
                    "type_of_rate": pl.Utf8,
                    "time_zone": pl.Utf8,
                    "point_of_delivery_balancing_authority": pl.Utf8,
                    "point_of_delivery_specific_location": pl.Utf8,
                    "class_name": pl.Utf8,
                    "term_name": pl.Utf8,
                    "increment_name": pl.Utf8,
                    "increment_peaking_name": pl.Utf8,
                    "product_name": pl.Utf8,
                    "rate_units": pl.Utf8,
                    "transaction_quantity": pl.Utf8,
                    "price": pl.Utf8,
                    "standardized_quantity": pl.Utf8,
                    "standardized_price": pl.Utf8,
                    "total_transmission_charge": pl.Utf8,
                    "total_transaction_charge": pl.Utf8,
                    "transaction_begin_date": pl.Utf8,
                    "transaction_end_date": pl.Utf8,
                    "trade_date": pl.Utf8,
                    "FilingType": pl.Utf8,
                    "filing_type": pl.Utf8
                }
            else: # identity
                raw_dtypes = {
                    "filer_unique_id": pl.Utf8,
                    "company_name": pl.Utf8,
                    "company_identifier": pl.Utf8,
                    "contact_name": pl.Utf8,
                    "contact_email": pl.Utf8,
                    "contact_zip": pl.Utf8,
                    "contact_country_name": pl.Utf8,
                    "contact_phone": pl.Utf8,
                    "filing_quarter": pl.Utf8
                }
            
            df = pl.read_csv(tmp_csv_path, ignore_errors=True, dtypes=raw_dtypes)

            if table_type == "transactions":
                # Normalize filing_type column name
                if "FilingType" in df.columns and "filing_type" not in df.columns:
                    df = df.rename({"FilingType": "filing_type"})
                
                date_cols = ["transaction_begin_date", "transaction_end_date"]
                float_cols = ["transaction_quantity", "price", "standardized_quantity", "standardized_price", "total_transmission_charge", "total_transaction_charge"]
                
                for col in date_cols:
                    if col in df.columns:
                        df = df.with_columns(pl.col(col).str.to_datetime("%Y%m%d%H%M", strict=False))
                
                if "trade_date" in df.columns:
                    df = df.with_columns(pl.col("trade_date").str.to_datetime("%Y%m%d", strict=False).cast(pl.Datetime("us")))

                for col in float_cols:
                    if col in df.columns:
                        df = df.with_columns(pl.col(col).cast(pl.Float64, strict=False))
            
            return df
        finally:
            if os.path.exists(tmp_csv_path):
                os.remove(tmp_csv_path)

def write_parquet_with_metadata(df: pl.DataFrame, output_path: Path, company_id: str, company_name: str, extra_metadata: dict = None):
    """
    Helper to write a Polars DataFrame to Parquet with PyArrow metadata branding.
    """
    table = df.to_arrow()
    existing_metadata = table.schema.metadata or {}
    
    # Combined metadata
    combined_meta = {
        **existing_metadata,
        b"company_id": str(company_id).encode("utf-8"),
        b"company_name": str(company_name).encode("utf-8")
    }
    
    if extra_metadata:
        for k, v in extra_metadata.items():
            combined_meta[str(k).encode("utf-8")] = str(v).encode("utf-8")
            
    table = table.replace_schema_metadata(combined_meta)
    pq.write_table(table, output_path)

def persist_to_lake(dfs: dict[str, pl.DataFrame], base_lake_path: str, year_quarter: str, company_id: str, company_name: str = "Unknown"):
    """
    Writes the DataFrames to the partitioned Parquet lake.
    """
    partition_path = Path(base_lake_path) / f"year_quarter={year_quarter}" / f"company_id={company_id}"
    partition_path.mkdir(parents=True, exist_ok=True)
    
    if 'transactions' in dfs:
        output_file = partition_path / "transactions.parquet"
        write_parquet_with_metadata(dfs['transactions'], output_file, company_id, company_name)
        print(f"Transactions persisted to: {output_file}")
    
    if 'identity' in dfs:
        output_file = partition_path / "ident.parquet"
        write_parquet_with_metadata(dfs['identity'], output_file, company_id, company_name)
        print(f"Identity metadata persisted to: {output_file}")


"""
If you want to call this from the command line use the following main function:

"""
if __name__ == "__main__":
    # Example usage
    MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
    LOOKUP_PATH = "data/lake/filing_lookup.parquet"
    
    if not os.path.exists(LOOKUP_PATH):
        print("Error: Lookup table missing. Run discovery first.")
    else:
        lookup = pl.read_parquet(LOOKUP_PATH)
        sample = lookup.head(1).to_dicts()[0]
        print(f"Hardened ingestion for: {sample['company_name']}")
        
        dfs = stream_filing_to_polars(MASTER_ZIP, sample['sub_zip_name'])
        if dfs:
            persist_to_lake(
                dfs, 
                "data/lake", 
                sample['year_quarter'], 
                sample['company_id'], 
                sample['company_name']
            )
