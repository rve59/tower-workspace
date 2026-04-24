import polars as pl
import os
from pathlib import Path
from glob import glob

LAKE_DIR = "data/lake/transactions"

def migrate_lake():
    print(f"Starting Lake Migration: {LAKE_DIR}")
    
    # 1. Gather all transaction files
    parquet_files = glob(os.path.join(LAKE_DIR, "**/*.parquet"), recursive=True)
    print(f"Found {len(parquet_files)} partitions to migrate.")
    
    for pf in parquet_files:
        print(f"Migrating: {pf}")
        try:
            # Read existing data
            df = pl.read_parquet(pf)
            
            # Map columns to ensure perfect schema alignment
            # (Dates as Datetime, Qty as Float64)
            date_cols = ["transaction_begin_date", "transaction_end_date"]
            float_cols = ["transaction_quantity", "price", "standardized_quantity", "standardized_price", "total_transmission_charge", "total_transaction_charge"]
            
            for col in date_cols:
                if col in df.columns:
                    # If it's already a date, this is a no-op, if it's int or string, we parse
                    if df[col].dtype == pl.Int64:
                        df = df.with_columns(pl.col(col).cast(pl.Utf8).str.to_datetime("%Y%m%d%H%M", strict=False))
                    elif df[col].dtype == pl.Utf8:
                        df = df.with_columns(pl.col(col).str.to_datetime("%Y%m%d%H%M", strict=False))
            
            if "trade_date" in df.columns:
                # Force to Datetime('us') regardless of current dtype
                df = df.with_columns(pl.col("trade_date").cast(pl.Utf8, strict=False).str.to_datetime("%Y%m%d", strict=False).cast(pl.Datetime("us")))

            for col in float_cols:
                if col in df.columns:
                    df = df.with_columns(pl.col(col).cast(pl.Float64, strict=False))
            
            # --- TRACEABILITY HARMONIZATION ---
            if "source_row_index" not in df.columns:
                df = df.with_row_index("source_row_index")
            if "source_filename" not in df.columns:
                # Use the company_id or path relative as a fallback filename
                df = df.with_columns(source_filename = pl.lit(os.path.basename(pf)))
            
            # Save back with the uniform schema
            df.write_parquet(pf)
            
        except Exception as e:
            print(f"ERROR migrating {pf}: {e}")

    print("\nMigration Complete. Lake schema is now uniform.")

if __name__ == "__main__":
    migrate_lake()
