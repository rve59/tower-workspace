import polars as pl
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.rules.eqr import run_all_direct_rules

def validate_parquet_lake(lake_root: str):
    """
    Scans the Parquet lake for all transaction files and executes validation rules.
    """
    print(f"--- Global Lake Validation ---")
    print(f"Scanning lake at: {lake_root}")
    
    # Use glob pattern to catch all partitioned Parquet files
    parquet_pattern = os.path.join(lake_root, "**", "transactions.parquet")
    
    try:
        # Lazy scan for performance across multiple files
        # hive_partitioning=True allows us to automatically include year_quarter and company_id columns
        df_lazy = pl.scan_parquet(parquet_pattern, hive_partitioning=True)
        
        # Inject Traceability if not already present (Parquet should have source_meta)
        # Note: Polars LazyFrame doesn't support with_row_index directly in the same way 
        # unless collected or using specific expressions. 
        # For now, we rely on the row indices stored during ingestion.
        
        # Compute row count
        count_df = df_lazy.select(pl.len()).collect()
        total_rows = count_df.item()
        print(f"Total Transactions in Lake: {total_rows:,}")
        
        if total_rows == 0:
            print("Warning: No transactions found in the lake.")
            return

        # Execute Rules
        print("Executing TOWER-K Validation Rules across all partitions...")
        # Since run_all_direct_rules might involve operations that benefit from Eager execution, 
        # or we want to leverage Lazy execution for the whole plan:
        # We can pass the LazyFrame if the rules support it, or collect first.
        # Our current rules support both (mostly filtering and arithmetic).
        
        df_eager = df_lazy.collect()
        errors = run_all_direct_rules(df_eager)
        
        if errors.height == 0:
            print("\u2705 ALL RULES PASSED ACROSS LAKE")
        else:
            print(f"\u274c FAILED: {errors.height:,} errors found in the lake.")
            
            # Summary by Company and Rule
            summary = errors.group_by(["rule_id", "company_id"]).agg(pl.len().alias("error_count"))
            print("\nError Summary by Entity:")
            print(summary.sort("error_count", descending=True))
            
            # Save global error report
            report_path = "data/reports/global_validation_report.parquet"
            os.makedirs("data/reports", exist_ok=True)
            errors.write_parquet(report_path)
            print(f"\nGlobal error report saved to: {report_path}")

    except Exception as e:
        print(f"Error during lake validation: {e}")

if __name__ == "__main__":
    LAKE_ROOT = "data/lake/transactions"
    validate_parquet_lake(LAKE_ROOT)
