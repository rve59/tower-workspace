import polars as pl
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.ingest.streaming import stream_filing_to_polars, persist_to_lake

MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
LOOKUP_PATH = "data/lake/filing_lookup.parquet"

# Target 15 Substantial Companies
TARGET_IDS = [
    "6486775", "6444535", "6443093", "6442933", "6442515", 
    "6438859", # LARGE
    "6429962", "6412333", "6412317", "6412300", 
    "6368704", # LARGE
    "6356586", "6310799", "6281194", "6278165"
]

def mass_ingest():
    if not os.path.exists(LOOKUP_PATH):
        print("Error: Lookup table missing.")
        return

    lookup = pl.read_parquet(LOOKUP_PATH)
    
    # Filter for our 15 targets in the 2025Q1 period
    filings = lookup.filter(
        (pl.col("company_id").is_in(TARGET_IDS)) & 
        (pl.col("year_quarter") == "2025Q1")
    ).to_dicts()
    
    print(f"Found {len(filings)} filings to process.")
    
    total_rows = 0
    for f in filings:
        print(f"\n>>> Processing: {f['company_name']} ({f['company_id']})")
        try:
            # 1. Ingest (Streaming)
            df = stream_filing_to_polars(MASTER_ZIP, f['sub_zip_name'])
            
            if df is None or df.height == 0:
                print(f"Skipping {f['company_id']} - No data.")
                continue
                
            # Inject Traceability
            df = df.with_row_index("source_row_index")
            df = df.with_columns(source_filename = pl.lit(f['sub_zip_name']))
            
            # 2. Persist to Lake
            persist_to_lake(df, "data/lake/transactions", f['year_quarter'], f['company_id'])
            
            total_rows += df.height
            print(f"Ingested {df.height:,} transactions. Current session total: {total_rows:,}")
            
        except Exception as e:
            print(f"FAILED to process {f['company_id']}: {e}")

    print(f"\nDONE. Mass Ingestion complete. Total new rows: {total_rows:,}")

if __name__ == "__main__":
    mass_ingest()
