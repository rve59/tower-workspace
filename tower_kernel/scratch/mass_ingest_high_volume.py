import polars as pl
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.ingest.streaming import stream_filing_to_polars, persist_to_lake

MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
LOOKUP_PATH = "data/lake/filing_lookup.parquet"

# Top 10 Largest Filers (Targeting 50M+ rows)
BIG_FISH_IDS = [
    "5992335", "6052375", "6153783", "6120645", "5949160", 
    "6037910", "6438859", "6108872", "6077556", "5963190"
]

def ingest_high_volume():
    if not os.path.exists(LOOKUP_PATH):
        print("Error: Lookup table missing.")
        return

    lookup = pl.read_parquet(LOOKUP_PATH)
    
    # Filter for our "Big Fish" in the 2025Q1 period
    filings = lookup.filter(
        (pl.col("company_id").is_in(BIG_FISH_IDS)) & 
        (pl.col("year_quarter") == "2025Q1")
    ).to_dicts()
    
    print(f"Found {len(filings)} high-volume filings to process.")
    
    total_new_rows = 0
    for f in filings:
        print(f"\n>>> [HIGH VOLUME] Processing: {f['company_name']} ({f['company_id']})")
        try:
            # 1. Ingest (Streaming with hardened schema)
            df = stream_filing_to_polars(MASTER_ZIP, f['sub_zip_name'])
            
            if df is None or df.height == 0:
                print(f"Skipping {f['company_id']} - No data.")
                continue
                
            # Inject Traceability
            df = df.with_row_index("source_row_index")
            df = df.with_columns(source_filename = pl.lit(f['sub_zip_name']))
            
            # 2. Persist to Lake
            persist_to_lake(df, "data/lake/transactions", f['year_quarter'], f['company_id'])
            
            total_new_rows += df.height
            print(f"Ingested {df.height:,} transactions. Session total: {total_new_rows:,}")
            
        except Exception as e:
            print(f"FAILED to process {f['company_id']}: {e}")

    print(f"\nDONE. High-Volume Ingestion complete. Total new rows: {total_new_rows:,}")

if __name__ == "__main__":
    ingest_high_volume()
