import polars as pl
import sys
import os
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from tower_kernel.rules.eqr import run_benchmarked_validation

def main():
    # Load High-Volume Global Lake
    lake_path = "data/lake/transactions/**/*.parquet"
    
    print(f"Loading Global Lake: {lake_path}")
    
    # Use scan_parquet for true streaming on 50M+ rows
    ldf = pl.scan_parquet(lake_path)
    
    engine = sys.argv[2] if len(sys.argv) > 2 else "cpu"
    print(f"Executing Global Ruleset (Engine: {engine})...")
    
    errors, stats = run_benchmarked_validation(ldf, engine=engine)
    
    # Save stats separately based on engine
    filename = f"instrumentation_results_{engine}.json"
    with open(filename, "w") as f:
        json.dump(stats, f, indent=2)
    
    # Group by category for a summary table
    stats_df = pl.DataFrame(stats)
    print("\nInstrumentation Results (Grouped by Category):")
    summary = stats_df.group_by("category").agg([
        pl.len().alias("rule_count"),
        pl.col("duration_ms").sum().alias("total_duration_ms"),
        pl.col("error_count").sum().alias("total_errors"),
        pl.col("throughput_tps").mean().alias("avg_throughput_tps")
    ])
    print(summary)
    
    print("\nDetailed breakdown saved to 'instrumentation_results.json'")

if __name__ == "__main__":
    main()
