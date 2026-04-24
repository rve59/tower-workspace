import polars as pl
from tower_kernel.rules.eqr import run_benchmarked_validation

def test_filing_type_consistency():
    # Mock data lacks filing_type, engine will inject "NEW"
    data = {
        "transaction_unique_id": ["T1", "T2"],
        "seller_company_name": ["Seller A", "Seller A"]
    }
    ldf = pl.LazyFrame(data)
    
    print("\n--- Test 1: NEW Filing with Implicit NEW Rows (PASS) ---")
    errors_df, _ = run_benchmarked_validation(
        ldf, 
        metadata={"filing_type": "NEW"},
        engine="cpu"
    )
    # D.3.9.1 should pass because missing rows default to NEW
    # We filter by Category STRUCTURAL to see D.3.9.x
    structural_errs = errors_df.filter(pl.col("category") == "STRUCTURAL")
    print(f"Structural Errors found: {structural_errs.height}")
    assert structural_errs.height == 0

    print("\n--- Test 2: NEW Filing with Mixed Rows (FAIL D.3.9.1) ---")
    data_mixed = {
        "transaction_unique_id": ["T1", "T2"],
        "filing_type": ["NEW", "DELETE"] # T2 is invalid for a NEW filing
    }
    ldf_mixed = pl.LazyFrame(data_mixed)
    errors_df, _ = run_benchmarked_validation(
        ldf_mixed, 
        metadata={"filing_type": "NEW"},
        engine="cpu"
    )
    structural_errs = errors_df.filter(pl.col("rule_id") == "D.3.9.1")
    print(f"D.3.9.1 Errors found: {structural_errs.height}")
    assert structural_errs.height == 1

    print("\n--- Test 3: DELETE Filing with Transactions (FAIL D.3.9.3) ---")
    errors_df, _ = run_benchmarked_validation(
        ldf, 
        metadata={"filing_type": "DELETE"},
        engine="cpu"
    )
    structural_errs = errors_df.filter(pl.col("rule_id") == "D.3.9.3")
    print(f"D.3.9.3 Errors found: {structural_errs.height}")
    assert structural_errs.height == 2 # Both rows are rejected in DELETE mode

    print("\n--- Test 4: Invalid Row-Level Filing Type (FAIL D.3.1.2) ---")
    data_invalid = {
        "transaction_unique_id": ["T1"],
        "filing_type": ["INVALID_MODE"]
    }
    ldf_invalid = pl.LazyFrame(data_invalid)
    errors_df, _ = run_benchmarked_validation(
        ldf_invalid,
        metadata={"filing_type": "NEW"},
        engine="cpu"
    )
    structural_errs = errors_df.filter(pl.col("rule_id") == "D.3.1.2")
    print(f"D.3.1.2 Errors found: {structural_errs.height}")
    assert structural_errs.height == 1

    print("\nSUCCESS: All Filing Type consistency rules verified.")

if __name__ == "__main__":
    test_filing_type_consistency()
