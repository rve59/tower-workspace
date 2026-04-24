import polars as pl
import datetime
from tower_kernel.rules.eqr import METADATA_RULES, run_benchmarked_validation, RegistryRuleRegistry

def test_expanded_rules():
    # 1. Create a draft with multiple non-structural violations
    data = pl.DataFrame({
        "transaction_unique_id": ["T_GOOD", "T_HIGH_PRICE", "T_NEG_QTY", "T_BAD_CAPACITY", "T_BAD_EMAIL", "T_BAD_AFFILIATE", "T_BAD_DATE"],
        "price": [10.0, 2000.0, 10.0, 50.0, 10.0, 10.0, 10.0],
        "transaction_quantity": [100.0, 100.0, -5.0, 100.0, 100.0, 100.0, 100.0],
        "rate_units": ["$/MWH", "$/MWH", "$/MWH", "$/MWH", "$/MWH", "$/MWH", "$/MWH"],
        "product_name": ["ENERGY", "ENERGY", "ENERGY", "CAPACITY", "ENERGY", "ENERGY", "ENERGY"],
        "contact_email": ["test@example.com", "test@example.com", "test@example.com", "test@example.com", "bad-email", "test@example.com", "test@example.com"],
        "contract_affiliate": ["Y", "Y", "Y", "Y", "Y", "INVALID", "Y"],
        "transaction_begin_date": [datetime.date(2024, 1, 1)] * 6 + [datetime.date(1800, 1, 1)],
        
        # Required fields to satisfy other structural rules and avoid noise
        "contract_unique_id": ["C1"] * 7,
        "seller_company_name": ["TEST"] * 7,
        "product_type_name": ["ENERGY"] * 7,
        "total_transaction_charge": [1000.0, 200000.0, -50.0, 5000.0, 1000.0, 1000.0, 1000.0],
        "total_transmission_charge": [0.0] * 7,
        "transaction_end_date": [datetime.date(2024, 1, 2)] * 7,
        "class_name": ["OS"] * 7,
        "term_name": ["S"] * 7,
        "increment_name": ["H"] * 7,
        "increment_peaking_name": ["P"] * 7,
        "time_zone": ["PST"] * 7,
        "point_of_delivery_balancing_authority": ["PJM"] * 7,
        "point_of_delivery_specific_location": ["HUB"] * 7,
        "ferc_tariff_reference": ["TARIFF"] * 7,
        "trade_date": [datetime.date(2024, 1, 1)] * 7,
        "type_of_rate": ["F"] * 7,
        "standardized_price": [10.0] * 7,
        "standardized_quantity": [100.0] * 7,
        "source_filename": ["test.zip"] * 7,
        "source_row_index": list(range(1, 8))
    })

    ldf = data.lazy()
    
    # 2. Run validation
    # We mock registry_ldf to avoid CID lookup failures during this test
    registry_ldf = pl.DataFrame({"cid": ["TEST"], "legal_name": ["TEST"], "effective_start_date": [datetime.date(1900, 1, 1)], "effective_end_date": [None]}).lazy()
    
    errors_df, results = run_benchmarked_validation(
        ldf, 
        registry_ldf=registry_ldf, 
        metadata={"company_id": "TEST", "filing_date": datetime.date(2024, 4, 1)}
    )
    
    # 3. Analyze results
    print("\n--- Expanded Rule Validation Results ---")
    findings = {}
    for rule_res in results:
        if rule_res["error_count"] > 0:
            findings[rule_res["rule_id"]] = rule_res["error_count"]
            print(f"Rule {rule_res['rule_id']} ({rule_res['category']}): {rule_res['error_count']} errors found.")

    # Assertions for our target rules
    assert "F.17.8.1" in findings  # High Price
    assert "F.25.21.2" in findings # Non-positive Qty
    assert "F.17.4.2" in findings  # Capacity unit mismatch
    assert "F.16.8" in findings    # Bad Email
    assert "F.21.5" in findings    # Bad Affiliate
    assert "F.20.3" in findings    # Bad Date
    
    print("\nSUCCESS: All non-structural rules verified.")

if __name__ == "__main__":
    test_expanded_rules()
