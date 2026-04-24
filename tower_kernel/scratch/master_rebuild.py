import polars as pl
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.ingest.streaming import stream_filing_to_polars, persist_to_lake

MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
LOOKUP_PATH = "data/lake/filing_lookup.parquet"

# MASTER LIST: Combining all filers for the 53M benchmark
ALL_FILER_IDS = [
    "6446663", # Original
    "6486775", "6444535", "6443093", "6442933", "6442515", "6438859", 
    "6429962", "6412333", "6412317", "6412300", "6368704", "6356586", 
    "6310799", "6281194", "6278165", "5992335", "6052375", "6153783", 
    "6120645", "5949160", "6037910", "6108872", "6077556", "5963190", 
    "6155459", "6172087", "5978947", "6069192", "5910835"
]

def rebuild_lake():
    if not os.path.exists(LOOKUP_PATH):
        print("Error: Lookup table missing.")
        return

    lookup = pl.read_parquet(LOOKUP_PATH)
    filings = lookup.filter(
        (pl.col("company_id").is_in(ALL_FILER_IDS)) & 
        (pl.col("year_quarter") == "2025Q1")
    ).to_dicts()
    
    print(f"Starting pristine rebuild for {len(filings)} filings (Target: 53M+ rows)...")
    
    total_rows = 0
    for f in filings:
        print(f"\n>>> Rebuilding: {f['company_name']} ({f['company_id']})")
        try:
            df = stream_filing_to_polars(MASTER_ZIP, f['sub_zip_name'])
            if df is not None:
                # Inject Traceability
                df = df.with_row_index("source_row_index")
                df = df.with_columns(source_filename = pl.lit(f['sub_zip_name']))
                
                persist_to_lake(df, "data/lake/transactions", f['year_quarter'], f['company_id'], company_name=f['company_name'])
                total_rows += df.height
                print(f"Successfully ingested {df.height:,} rows. Lake Total: {total_rows:,}")
        except Exception as e:
            print(f"FAILED {f['company_id']}: {e}")

    print(f"\nREBUILD COMPLETE. Final Global Row Count: {total_rows:,}")

if __name__ == "__main__":
    rebuild_lake()
