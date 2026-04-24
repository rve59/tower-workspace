import polars as pl
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.ingest.streaming import stream_filing_to_polars, persist_to_lake
from tower_kernel.rules.eqr import run_all_direct_rules

def run_pipeline(company_id: str = None):
    MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
    LOOKUP_PATH = "data/lake/filing_lookup.parquet"
    
    if not os.path.exists(LOOKUP_PATH):
        print("Error: Lookup table missing. Run discovery first.")
        return

    lookup = pl.read_parquet(LOOKUP_PATH)
    
    if company_id:
        filing = lookup.filter(pl.col("company_id") == company_id).head(1).to_dicts()
    else:
        # Default to a known decent sized sample
        filing = lookup.filter(pl.col("sub_zip_name").str.contains("6446663")).to_dicts()
    
    if not filing:
        print(f"Error: Company ID {company_id} not found.")
        return
        
    f = filing[0]
    print(f"--- Pipeline Execution for: {f['company_name']} ({f['company_id']}) ---")
    
    # 1. Ingest (Streaming)
    print(f"Step 1: Streaming CSV from nested zip...")
    df = stream_filing_to_polars(MASTER_ZIP, f['sub_zip_name'])
    
    if df is None or df.height == 0:
        print("Error: No data ingested.")
        return
    
    # 2. Map Column Names (CSV columns might be different from Parquet model names)
    # The CSV column names are often numeric (Field 1, Field 2...) 
    # but the sample CSVs I peeked at had names like 'transaction_unique_id'.
    # I'll normalize them.
    
    # Inject Traceability
    df = df.with_row_index("source_row_index")
    df = df.with_columns(
        source_filename = pl.lit(f['sub_zip_name'])
    )
    
    print(f"Successfully ingested {df.height:,} transactions.")
    
    # NEW: Persist to Lake
    print(f"Step 2: Persisting to Parquet Lake...")
    persist_to_lake(df, "data/lake/transactions", f['year_quarter'], f['company_id'])
    
    # 3. Validate
    print(f"Step 3: Executing TOWER-K Validation Rules...")
    # My rules expect specific column names. I'll ensure they are present.
    # Note: CSV ingestion column names might need mapping. 
    # For this demo, we assume the CSV schema matches the Parquet schema.
    
    errors = run_all_direct_rules(df)
    
    # 4. Results
    print(f"--- Results ---")
    if errors.height == 0:
        print("\u2705 ALL RULES PASSED")
    else:
        print(f"\u274c FAILED: {errors.height:,} errors found.")
        print(errors.group_by("rule_id").agg(pl.len().alias("count")))
        
        # Show a few traces
        print("\nTraceability Sample (First 5 errors):")
        print(errors.select(["rule_id", "transaction_unique_id", "source_row_index"]).head(5))

if __name__ == "__main__":
    # If a company_id is provided as arg
    cid = sys.argv[1] if len(sys.argv) > 1 else None
    run_pipeline(cid)
