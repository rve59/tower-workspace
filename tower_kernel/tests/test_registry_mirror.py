import polars as pl
import os
import pyarrow.parquet as pq
import datetime
from pathlib import Path
from tower_kernel.services.diagnostic import DiagnosticService
from tower_kernel.services.registry_mirror import RegistryMirrorService
from tower_kernel.ingest.streaming import write_parquet_with_metadata

LAKE_DIR = "data/lake/filer_id=TEST_REG/year=2024/quarter=1"
DRAFT_DIR = "data/workspace/drafts/user_id=test/session_id=registry_test/draft.parquet"

def setup_test_registry():
    # 1. Initialize Registry
    RegistryMirrorService.bootstrap_sample_data()
    # Add a specific test case CID: TEST_CID, Name: "Official Legal Name"
    temp_csv = "data/master/registry/temp_update.csv"
    with open(temp_csv, "w") as f:
        f.write("cid,legal_name,effective_start_date,effective_end_date\n")
        f.write("TEST_CID,Official Legal Name,2020-01-01,\n")
    
    RegistryMirrorService.import_registry(temp_csv)
    os.remove(temp_csv)

def setup_draft_data(cid, seller_name):
    # 2. Create a draft branded with the CID
    df = pl.DataFrame({
        "transaction_unique_id": ["T1"],
        "contract_unique_id": ["C1"],
        "seller_company_name": [seller_name],
        "product_name": ["ENERGY"],
        "rate_units": ["$/MWH"],
        "total_transaction_charge": [100.0],
        "total_transmission_charge": [0.0],
        "transaction_quantity": [1.0],
        "price": [100.0],
        "transaction_begin_date": [datetime.date(2024, 1, 1)],
        "transaction_end_date": [datetime.date(2024, 1, 2)],
        "class_name": ["OS"],
        "term_name": ["S"],
        "increment_name": ["H"],
        "increment_peaking_name": ["P"],
        "time_zone": ["PST"],
        "point_of_delivery_balancing_authority": ["PJM"],
        "point_of_delivery_specific_location": ["HUB"],
        "ferc_tariff_reference": ["TARIFF"],
        "trade_date": [datetime.date(2024, 1, 1)],
        "type_of_rate": ["F"],
        "standardized_price": [100.0],
        "standardized_quantity": [1.0],
        "source_filename": ["test.zip"],
        "source_row_index": [1]
    })
    
    os.makedirs(os.path.dirname(DRAFT_DIR), exist_ok=True)
    write_parquet_with_metadata(
        df, 
        Path(DRAFT_DIR), 
        cid, 
        "Test Common Name",
        extra_metadata={"year": "2024", "quarter": "1"}
    )

def test_registry_validation():
    print("\n=== TOWER-K Registry Validation Test ===")
    setup_test_registry()
    
    # Case 1: CID not in registry
    print("\nTest 1: Invalid CID (Non-Existent)")
    setup_draft_data("UNKNOWN_CID", "Some Name")
    scorecard = DiagnosticService.get_compliance_scorecard(DRAFT_DIR)
    
    f1631 = next(s for s in scorecard["scorecard"] if s["rule_id"] == "F.16.3.1")
    print(f"Rule F.16.3.1 Error Count: {f1631['error_count']} (Expected: 1)")
    assert f1631["error_count"] > 0
    
    # Case 2: CID correct, but Name Mismatch
    print("\nTest 2: CID Valid, Name Mismatch")
    setup_draft_data("TEST_CID", "Mismatched Name Ltd")
    scorecard = DiagnosticService.get_compliance_scorecard(DRAFT_DIR)
    
    f1632 = next(s for s in scorecard["scorecard"] if s["rule_id"] == "F.16.3.2")
    print(f"Rule F.16.3.2 Error Count: {f1632['error_count']} (Expected: 1)")
    assert f1632["error_count"] > 0

    # Case 3: CID and Name correct
    print("\nTest 3: CID and Name Match (Valid)")
    setup_draft_data("TEST_CID", "Official Legal Name")
    scorecard = DiagnosticService.get_compliance_scorecard(DRAFT_DIR)
    
    f1631 = next(s for s in scorecard["scorecard"] if s["rule_id"] == "F.16.3.1")
    f1632 = next(s for s in scorecard["scorecard"] if s["rule_id"] == "F.16.3.2")
    print(f"Rule F.16.3.1 Errors: {f1631['error_count']}")
    print(f"Rule F.16.3.2 Errors: {f1632['error_count']}")
    assert f1631["error_count"] == 0
    assert f1632["error_count"] == 0
    
    print("\nSUCCESS: Registry Mirror validation functioning correctly.")

if __name__ == "__main__":
    test_registry_validation()
