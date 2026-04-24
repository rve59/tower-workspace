import polars as pl
import pyarrow.parquet as pq
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.ingest.streaming import write_parquet_with_metadata

LOOKUP_PATH = "data/lake/filing_lookup.parquet"
TRANSACTIONS_ROOT = "data/lake/transactions"

def repair_branding():
    print("=== TOWER-K Lake Correction: Metadata Branding ===")
    
    if not os.path.exists(LOOKUP_PATH):
        print("Error: Lookup table missing. Cannot correlate company names.")
        return
        
    lookup = pl.read_parquet(LOOKUP_PATH)
    # Create a mapping for fast lookup
    company_map = {row['company_id']: row['company_name'] for row in lookup.to_dicts()}
    
    # 1. Find all parquet files in the transactions lake
    parquet_files = list(Path(TRANSACTIONS_ROOT).rglob("*.parquet"))
    print(f"Found {len(parquet_files)} partitions to process.")
    
    for p_file in parquet_files:
        # Extract company_id from path: .../company_id=12345/transactions.parquet
        company_id = None
        for part in p_file.parts:
            if part.startswith("company_id="):
                company_id = part.split("=")[1]
                break
        
        if not company_id:
            print(f"Skip: Could not determine company_id for {p_file}")
            continue
            
        company_name = company_map.get(company_id, "Unknown Entity")
        print(f"Branding {company_id} ({company_name})...")
        
        try:
            # Load existing data
            df = pl.read_parquet(p_file)
            
            # Rewrite with metadata branding
            write_parquet_with_metadata(df, p_file, company_id, company_name)
        except Exception as e:
            print(f"Error processing {p_file}: {e}")

    print("\n=== Lake Correction Complete ===")

if __name__ == "__main__":
    repair_branding()
