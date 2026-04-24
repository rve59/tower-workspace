import os
import shutil
import polars as pl
from pathlib import Path
from tower_kernel import config
from tower_kernel.services.correction import CorrectionService

def test_bundle_ingestion():
    CID = "CID_BUNDLE_TEST"
    
    # 1. Setup Sandbox Inbox
    inbox_dir = config.get_tier_path(CID, config.TIER_INBOX)
    period_dir = inbox_dir / "2025" / "Q2"
    period_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"--- Setup: Creating multi-file bundle in {period_dir} ---")
    
    # Identification CSV
    ident_csv = period_dir / "ident_erp_export.csv"
    ident_csv.write_text("Seller,Seller Company Name,Contact Name\nTest Seller,Test Co,Jane Doe")
    
    # Contracts CSV
    contracts_csv = period_dir / "contracts_master.csv"
    contracts_csv.write_text("Contract Number,Customer Company Name,Contract Commencement Date\nC-100,Global Power,2025-01-01")
    
    # Transactions CSV
    trans_csv = period_dir / "transactions_incremental.csv"
    trans_csv.write_text("Transaction Unique ID,Seller Company Name,Price,Quantity\nTX-999,Test Co,50.5,100")
    
    # Index CSV
    index_csv = period_dir / "filing_index.csv"
    index_csv.write_text("Filer,Filer CID,Contact Name\nTest Filer,CID-1,John Admin")

    print("--- Execution: Processing Inbox ---")
    results = CorrectionService.process_inbox(CID)
    
    print(f"Processed {results['total_files']} files.")
    for res in results["results"]:
        print(f"  - {res['file']} -> {res['table']} | Status: {res['status']} | Period: {res['period']}")

    # 2. Verification
    print("--- Verification: Checking Bronze Tiers ---")
    bronze_base = config.get_tier_path(CID, config.TIER_BRONZE, year="2025", quarter="Q2")
    
    tables = {
        "ident": config.TABLE_IDENT,
        "contracts": config.TABLE_CONTRACTS,
        "transactions": config.TABLE_TRANSACTIONS,
        "index": config.TABLE_INDEX
    }
    
    for label, filename in tables.items():
        p_path = bronze_base / filename
        assert p_path.exists(), f"Missing expected parquet: {p_path}"
        
        df = pl.read_parquet(p_path)
        print(f"VERIFIED {label.upper()}: {df.height} rows found at {p_path.relative_to(config.PACKAGE_ROOT)}")
        
        # Verify metadata injection
        assert "filing_year" in df.columns, f"Missing filing_year in {label}"
        assert "filing_quarter" in df.columns, f"Missing filing_quarter in {label}"
        
        assert df["filing_year"][0] == "2025"
        assert df["filing_quarter"][0] == "2"
        
    print("\n✅ BUNDLE INGESTION TEST PASSED")

if __name__ == "__main__":
    try:
        # Cleanup previous test if any
        test_dir = config.LAKE_ROOT / "CID_BUNDLE_TEST"
        if test_dir.exists():
            shutil.rmtree(test_dir)
            
        test_bundle_ingestion()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
