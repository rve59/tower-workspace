import polars as pl
from pathlib import Path
from tower_kernel.ingest.master_extractor import FERCMasterExtractor
from tower_kernel.rules.eqr import run_benchmarked_validation
import os
import shutil

# --- SETUP MOCK MASER DATA ---
mock_master_dir = Path("tower_kernel/data/historic/CSV_2025_Q1")
mock_master_dir.mkdir(parents=True, exist_ok=True)
zip_path = mock_master_dir / "CSV_2025_Q1_6446663_1723143.ZIP"

def create_mock_zip():
    import zipfile
    import io
    
    # Dirty Transactions (Title Case FERC Aliases)
    tx_csv = """Transaction Unique ID,Seller,Customer Company Name,FERC Tariff Reference,Contract Service Agreement ID,Transaction Identifier,Transaction Begin Date,Transaction End Date,Trade Date,Type of Rate,Time Zone,PODBAA,Class Name,Term Name,Increment Name,Increment Peaking Name,Product Name,Transaction Quantity,Price,Rate Units,Total Transmission Charge,Total Transaction Charge
TX_001,UTILITY_A,CUST_X,FERC_1,CONTRACT_1,ID_001,202501010000,202501010100,20250101,Fixed,ED,PJM,F,LT,H,P,ENERGY,100,50,$/MWH,0,5000
TX_DIRTY,UTILITY_A,CUST_X,FERC_1,CONTRACT_1,ID_002,202501010000,202501010100,20250101,Fixed,ED,PJM,F,LT,H,P,ENERGY,BAD_QUANTITY,50,$/MWH,0,5000
TX_DATE_DIRTY,UTILITY_A,CUST_X,FERC_1,CONTRACT_1,ID_003,NOT_A_DATE,202501010100,20250101,Fixed,ED,PJM,F,LT,H,P,ENERGY,100,50,$/MWH,0,5000
"""

    # Contracts
    contracts_csv = """Contract Unique ID,Seller,Customer is RTO/ISO,Customer Company Name,Contract Affiliate,FERC Tariff Reference,Contract Service Agreement ID,Contract Execution Date,Commencement Date of Contract Terms,Contract Termination Date,Actual Termination Date,Extension Provision Description,Class Name,Term Name,Increment Name,Increment Peaking Name,Product Type,Product Name,Quantity,Units,Rate,Rate Minimum,Rate Maximum,Rate Description,Rate Units,PORBAA,PORSL,PODBAA,PODSL,Begin Date,End Date,Product Name Description
CONTRACT_1,UTILITY_A,N,CUST_X,N,FERC_1,CONTRACT_1,20240101,20240101,,,NONE,F,LT,H,P,CB,ENERGY,1000,MWH,50,40,60,FIXED,$/MWH,PJM,,PJM,,20240101,20251231,
"""

    # Ident
    ident_csv = """Seller,Seller CID,Seller Contact,Seller Contact Phone,Seller Contact Email,Filing Quarter,Filing Year,Qualifying Facility,Notes
UTILITY_A,C6446663,JOHN DOE,555-0199,john@utility.com,1,2025,N,TEST
"""

    with zipfile.ZipFile(zip_path, 'w') as z:
        z.writestr("transactions.csv", tx_csv)
        z.writestr("contracts.csv", contracts_csv)
        z.writestr("ident.csv", ident_csv)

print("Creating mock zip data...")
create_mock_zip()

# --- EXECUTE EXTRACTION ---
print("\nExecuting FERCMasterExtractor (Bronze Ingestion)...")
# First, ensure registry has our CID
mirror_path = Path("tower_kernel/data/master/registry/cid_master.parquet")
mirror_path.parent.mkdir(parents=True, exist_ok=True)
pl.DataFrame([
    {"cid": "6446663", "technical_id": "1723143", "legal_name": "UTILITY_A", "effective_start_date": "2000-01-01", "effective_end_date": None}
]).write_parquet(mirror_path)

extractor = FERCMasterExtractor("2025", "1", "6446663")
extractor.extract()

# --- EXECUTE VALIDATION ---
print("\nRunning Validation Engine on Bronze Lake...")
data_path = Path("tower_kernel/data/lake/filer_id=6446663/year=2025/quarter=1/data.parquet")
df = pl.read_parquet(data_path)
print(f"Ingested Rows: {df.height}")
print(f"Transaction Quantity for TX_DIRTY: '{df.filter(pl.col('transaction_unique_id') == 'TX_DIRTY')['transaction_quantity'][0]}'")

errors, stats = run_benchmarked_validation(df.lazy())

print(f"\nTotal Errors Found: {errors.height}")
print("Sample Error Details:")
print(errors.select(["transaction_unique_id", "rule_id", "error_message"]).head(10))

# Verify specific type errors
type_errors = errors.filter(pl.col("rule_id").str.contains("V4.TYPE"))
print(f"\nType Specific Errors: {type_errors.height}")
print(type_errors)

# cleanup
# shutil.rmtree("tower_kernel/data/lake/filer_id=6446663")
