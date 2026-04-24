import polars as pl
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.rules.eqr import run_all_direct_rules

def main():
    parquet_path = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/2025_Q4_C000722/2025q4_transactions_C000722.parquet"
    
    print(f"Loading sample parquet: {os.path.basename(parquet_path)}")
    
    # 1. Load data
    df = pl.read_parquet(parquet_path)
    
    # 2. Inject Traceability Metadata
    df = df.with_row_index("source_row_index")
    df = df.with_columns(
        source_filename = pl.lit(os.path.basename(parquet_path))
    )
    
    print(f"Total Transactions: {df.height:,}")
    
    # 3. Execute Rules
    print("Executing EQR 'YES' Category Rules (F.24.6, F.17.2.2, F.24.3)...")
    start_time = datetime.now()
    errors = run_all_direct_rules(df)
    end_time = datetime.now()
    
    duration = (end_time - start_time).total_seconds()
    print(f"Validation completed in {duration:.4f} seconds.")
    
    # 4. Report
    if errors.height == 0:
        print("\u2705 All rules passed! No validation errors found.")
    else:
        print(f"\u274c Found {errors.height:,} validation errors.")
        
        # Group by rule for summary
        summary = errors.group_by("rule_id").agg(pl.len().alias("count"))
        print("\nError Summary:")
        print(summary)
        
        # Show sample errors with traceability
        print("\nSample Errors (Traceability detail):")
        print(errors.head(10))
        
        # Save to report artifact
        errors.write_parquet("eqr_validation_report_2025q4.parquet")
        print("\nFull error report saved to 'eqr_validation_report_2025q4.parquet'")

if __name__ == "__main__":
    main()
