import polars as pl
from pathlib import Path
from tower_kernel.services.lake_merger import LakeMergerService
from tower_kernel import config
import shutil

def verify_composite_key():
    cid = "test_cid_999"
    # Use the corrected config API
    lake_dir = config.get_tier_path(cid, config.TIER_BRONZE)
    master_path = lake_dir / config.TABLE_TRANSACTIONS

    # Clean start
    if master_path.exists():
        master_path.unlink()

    # Create initial master data (simulating a prior ingestion)
    initial_df = pl.DataFrame({
        "transaction_unique_id": ["T1"],
        "source_filename": ["initial_filing.csv"],
        "filing_type": ["MASTER"],
        "product_name": ["Energy"],
        # Add other columns expected by wide table
        "seller_company_id_ferc": ["S1"],
        "seller_company_name": ["Seller 1"],
        "customer_company_name": ["Cust A"],
        "contract_service_agreement_id": ["C1"],
        "seller_transaction_id": ["ST1"],
        "transaction_begin_date": [None],
        "transaction_end_date": [None],
        "trade_date": [None],
        "transaction_quantity": [100.0],
        "price": [50.0],
        "rate_units": ["$/MWh"],
        "standardized_quantity": [100.0],
        "standardized_price": [50.0],
        "total_transmission_charge": [0.0],
        "total_transaction_charge": [5000.0],
        "ingestion_timestamp": [None],
        "source_row_index": [0]
    })
    initial_df.write_parquet(master_path)
    print(f"Initial count: {initial_df.height}")

    # Create a 'correction' CSV with the SAME ID but different 'product_name'
    # 1. Test: Overwrite within same file (Surgery)
    csv1 = Path("correction_test_1.csv")
    pl.DataFrame({
        "transaction_unique_id": ["T1"],
        "source_filename": ["initial_filing.csv"], # TARGETING same file
        "product_name": ["Corrected Energy"]
    }).write_csv(csv1)
    
    LakeMergerService.upsert_transactions(cid, str(csv1))
    
    df = pl.read_parquet(master_path)
    print(f"Count after same-file correction: {df.height}") # Should still be 1
    print(f"Product name (same-file): {df.filter(pl.col('transaction_unique_id') == 'T1')['product_name'][0]}")
    
    # 2. Test: Append with different file (New filing with same ID)
    csv2 = Path("different_file.csv")
    pl.DataFrame({
        "transaction_unique_id": ["T1"],
        "source_filename": ["new_filing.csv"], # DIFFERENT file
        "product_name": ["New Filing Energy"]
    }).write_csv(csv2)
    
    LakeMergerService.upsert_transactions(cid, str(csv2))
    df = pl.read_parquet(master_path)
    print(f"Count after different-file append: {df.height}") # Should be 2 now
    
    # Cleanup
    csv1.unlink()
    csv2.unlink()

if __name__ == "__main__":
    verify_composite_key()
