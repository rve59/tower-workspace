import os
import sys
import polars as pl
import datetime
from pathlib import Path
import pyarrow.parquet as pq

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tower_kernel.services.diagnostic import DiagnosticService
from tower_kernel.ingest.streaming import write_parquet_with_metadata

LAKE_DIR = "data/lake/filer_id=TEST_FILER/year=2024/quarter=1"
DRAFT_DIR = "data/workspace/drafts/user_id=test/session_id=cross_q/draft.parquet"

def setup_test_data():
    os.makedirs(LAKE_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DRAFT_DIR), exist_ok=True)
    
    # 1. Create Q1 Lake Partition (Has Contract C1)
    q1_data = {
        "transaction_unique_id": ["T1_OLD"],
        "contract_unique_id": ["C1"],
        "seller_company_name": ["TEST_FILER"],
        "product_name": ["ENERGY"]
    }
    q1_df = pl.DataFrame(q1_data)
    q1_path = os.path.join(LAKE_DIR, "part-0.parquet")
    write_parquet_with_metadata(q1_df, q1_path, "TEST_FILER", "Test Filer Co", {"year": "2024", "quarter": "1"})
    
    # 2. Create Q2 Draft (Has Transaction T2 referencing C1, but C1 is MISSING in this draft)
    q2_data = {
        "transaction_unique_id": ["T2_NEW"],
        "contract_unique_id": ["C1"], # <--- References Q1 Contract
        "seller_company_name": ["TEST_FILER"],
        "product_name": ["ENERGY"],
        "rate_units": ["$/MWH"],
        "total_transaction_charge": [100.0],
        "total_transmission_charge": [0.0],
        "transaction_quantity": [1.0],
        "price": [100.0],
        "transaction_begin_date": [datetime.datetime(2024, 4, 1)],
        "transaction_end_date": [datetime.datetime(2024, 4, 1, 1)],
        "source_filename": ["draft.csv"],
        "source_row_index": [1],
        "class_name": ["F"],
        "term_name": ["S"],
        "increment_name": ["H"],
        "increment_peaking_name": ["P"],
        "time_zone": ["P"],
        "point_of_delivery_balancing_authority": ["CAISO"],
        "point_of_delivery_specific_location": ["LOC"],
        "ferc_tariff_reference": ["T1"],
        "trade_date": [datetime.datetime(2024, 4, 1)],
        "type_of_rate": ["FIXED"],
        "standardized_price": [100.0],
        "standardized_quantity": [1.0]
    }
    q2_df = pl.DataFrame(q2_data)
    write_parquet_with_metadata(q2_df, DRAFT_DIR, "TEST_FILER", "Test Filer Co", {"year": "2024", "quarter": "2"})
    
    print("Test data setup complete.")

def test_cross_quarter_validation():
    print("=== TOWER-K Sliding Window (Cross-Quarter) Validation Test ===")
    setup_test_data()
    
    # Execute validation
    print("\nRunning compliance scorecard for Q2 Draft...")
    result = DiagnosticService.get_compliance_scorecard(DRAFT_DIR)
    
    print(f"\nHistorical Context Found: {result['has_historical_context']}")
    
    # Find the Contract Continuity Rule in stats
    continuity_rule = next((s for s in result["scorecard"] if s["rule_id"] == "F.21.2.1-CONT"), None)
    
    if continuity_rule:
        print(f"Rule F.21.2.1-CONT: {continuity_rule['error_count']} violations found.")
        if continuity_rule["error_count"] == 0:
            print("SUCCESS: Transaction T2 successfully referenced Contract C1 from previous quarter.")
        else:
            print("FAIL: Transaction T2 failed to find Contract C1.")
    else:
        print("FAIL: Continuity Rule not executed.")

if __name__ == "__main__":
    test_cross_quarter_validation()
