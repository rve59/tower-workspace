import pytest
from pathlib import Path
import polars as pl
import shutil
from tower_kernel.ingest.ferc_historical_worker import FERCHistoricalIngestionWorker

def test_ferc_historical_ingestion_end_to_end():
    # Setup paths
    source_dir = Path("tower.docs/FERC EQR SAMPLES/compressed-folder")
    output_dir = Path("tower_kernel/data/lake_test")
    
    # Cleanup any previous runs
    if output_dir.exists():
        shutil.rmtree(output_dir)
        
    # Initialize worker
    worker = FERCHistoricalIngestionWorker(source_dir, output_dir)
    
    # Run ingestion
    worker.ingest_all()
    
    # Verify outputs
    assert (output_dir / "sellers" / "data.parquet").exists()
    assert (output_dir / "contracts" / "data.parquet").exists()
    assert (output_dir / "contract_terms" / "data.parquet").exists()
    assert (output_dir / "transactions").is_dir() # Partitioned
    
    # Check record counts (based on sample files)
    sellers_df = pl.read_parquet(output_dir / "sellers" / "data.parquet")
    assert sellers_df.height > 0
    
    tx_df = pl.read_parquet(output_dir / "transactions")
    assert tx_df.height > 0
    
    # Verify mapping
    print(f"Sellers height: {sellers_df.height}")
    print(f"Transactions height: {tx_df.height}")

if __name__ == "__main__":
    pytest.main([__file__])
