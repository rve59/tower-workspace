import os
import sys
import polars as pl
import datetime
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tower_kernel.rules.eqr import run_benchmarked_validation, METADATA_RULES, get_metadata_predicate

def test_lookup_rules():
    print("=== TOWER-K Lookup Rule Verification ===")
    
    # 1. Create a dummy dataframe with intentional lookup errors
    data = {
        "transaction_unique_id": ["E1", "E2", "E3", "G1"],
        "point_of_delivery_balancing_authority": ["CAISO", "INVALID_BA", "PJM", "MISO"],
        "rate_units": ["$/MWH", "INVALID_UNIT", "$/MW", "$/KV"],
        "product_name": ["ENERGY", "ENERGY", "CAPACITY", "ENERGY"],
        "class_name": ["F", "F", "F", "F"],
        "term_name": ["S", "S", "S", "S"],
        "increment_name": ["H", "H", "H", "H"],
        "increment_peaking_name": ["P", "P", "P", "P"],
        "time_zone": ["P", "P", "P", "P"],
        "point_of_delivery_specific_location": ["LOC1", "LOC1", "LOC1", "LOC1"],
        "seller_company_name": ["S1", "S1", "S1", "S1"],
        "ferc_tariff_reference": ["T1", "T1", "T1", "T1"],
        "trade_date": [datetime.datetime(2025, 1, 1)] * 4,
        "type_of_rate": ["FIXED", "FIXED", "FIXED", "FIXED"],
        "total_transaction_charge": [100.0, 100.0, 100.0, 100.0],
        "total_transmission_charge": [0.0, 0.0, 0.0, 0.0],
        "transaction_quantity": [1.0, 1.0, 1.0, 1.0],
        "price": [100.0, 100.0, 100.0, 100.0],
        "standardized_price": [100.0, 100.0, 100.0, 100.0],
        "standardized_quantity": [1.0, 1.0, 1.0, 1.0],
        "transaction_begin_date": [datetime.datetime(2025, 1, 1)] * 4,
        "transaction_end_date": [datetime.datetime(2025, 1, 1, 1)] * 4,
        "source_filename": ["test.csv"] * 4,
        "source_row_index": [1, 2, 3, 4],
        "product_type_name": ["ENERGY"] * 4,
        "contract_affiliate": ["Y"] * 4,
        "contact_email": ["test@example.com"] * 4
    }
    df = pl.DataFrame(data).lazy()
    
    # 2. Run validations
    errors_df, _ = run_benchmarked_validation(df, engine="cpu")
    
    print("\n[VALIDATION RESULTS]")
    if errors_df.height > 0:
        summary = errors_df.group_by("rule_id").len().sort("len", descending=True)
        print(summary)
        
        # Verify F.23.9 caught INVALID_BA
        ba_errors = errors_df.filter(pl.col("rule_id") == "F.23.9")
        if ba_errors.height > 0:
            print(f"\nCaught {ba_errors.height} Balancing Authority errors (F.23.9) in tracer.")
        
        # Verify F.23.5 caught INVALID_UNIT
        unit_errors = errors_df.filter(pl.col("rule_id") == "F.23.5")
        if unit_errors.height > 0:
            print(f"Caught {unit_errors.height} Rate Unit errors (F.23.5) in tracer.")
    else:
        print("No errors detected (Check if lookups are loading correctly).")

if __name__ == "__main__":
    test_lookup_rules()
