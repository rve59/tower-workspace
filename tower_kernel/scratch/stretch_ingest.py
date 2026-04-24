import polars as pl
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.ingest.streaming import stream_filing_to_polars, persist_to_lake

MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
LOOKUP_PATH = "data/lake/filing_lookup.parquet"

# Final batch to ensure we cross 50M
STRETCH_IDS = ["6105074", "5912895", "5992744", "6027315", "6102606"]

def ingest_stretch():
    lookup = pl.read_parquet(LOOKUP_PATH)
    filings = lookup.filter(
        (pl.col("company_id").is_in(STRETCH_IDS)) & 
        (pl.col("year_quarter") == "2025Q1")
    ).to_dicts()
    
    print(f"Ingesting {len(filings)} stretch filings...")
    
    for f in filings:
        print(f">>> Processing: {f['company_name']} ({f['company_id']})")
        df = stream_filing_to_polars(MASTER_ZIP, f['sub_zip_name'])
        if df is not None:
            df = df.with_row_index("source_row_index").with_columns(source_filename = pl.lit(f['sub_zip_name']))
            persist_to_lake(df, "data/lake/transactions", f['year_quarter'], f['company_id'])
            print(f"Ingested {df.height:,} transactions.")

if __name__ == "__main__":
    ingest_stretch()
