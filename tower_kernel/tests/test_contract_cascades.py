import polars as pl
from tower_kernel.rules.eqr import run_benchmarked_validation

def test_contract_cascades():
    print("\n--- Test A: Contract=NEW, Transactions=NEW (PASS) ---")
    data = {
        "transaction_unique_id": ["T1", "T2"],
        "contract_unique_id": ["C1", "C1"],
        "filing_type": ["NEW", "NEW"]
    }
    ldf = pl.LazyFrame(data)
    errors_df, _ = run_benchmarked_validation(ldf, engine="cpu")
    # D.3.9.6 should find 0 errors
    d396_errs = errors_df.filter(pl.col("rule_id") == "D.3.9.6")
    print(f"D.3.9.6 Errors found: {d396_errs.height}")
    assert d396_errs.height == 0

    print("\n--- Test B: Contract=NEW, One Transaction=DELETE (FAIL D.3.9.6) ---")
    data_mixed = {
        "transaction_unique_id": ["T1", "T2"],
        "contract_unique_id": ["C1", "C1"],
        "filing_type": ["NEW", "DELETE"]
    }
    ldf_mixed = pl.LazyFrame(data_mixed)
    errors_df, _ = run_benchmarked_validation(ldf_mixed, engine="cpu")
    d396_errs = errors_df.filter(pl.col("rule_id") == "D.3.9.6")
    print(f"D.3.9.6 Errors found: {d396_errs.height}")
    assert d396_errs.height == 1 # Found C1 has mixed types

    print("\n--- Test C: Contract=DELETE, Has Transactions (FAIL D.3.9.8) ---")
    data_delete = {
        "transaction_unique_id": ["T1", "T2"],
        "contract_unique_id": ["C1", "C1"],
        "filing_type": ["DELETE", "DELETE"]
    }
    ldf_delete = pl.LazyFrame(data_delete)
    errors_df, _ = run_benchmarked_validation(ldf_delete, engine="cpu")
    # D.3.9.8 should flag all rows as they belong to a DELETE contract
    d398_errs = errors_df.filter(pl.col("rule_id") == "D.3.9.8")
    print(f"D.3.9.8 Errors found: {d398_errs.height}")
    assert d398_errs.height == 2

    print("\n--- Test D: Heterogeneous Filing types across DIFFERENT contracts (PASS) ---")
    data_diff = {
        "transaction_unique_id": ["T1", "T2"],
        "contract_unique_id": ["C1", "C2"],
        "filing_type": ["NEW", "NOACTION"]
    }
    ldf_diff = pl.LazyFrame(data_diff)
    # This is allowed at the contract level (Merge mode logic)
    errors_df, _ = run_benchmarked_validation(ldf_diff, engine="cpu")
    d396_errs = errors_df.filter(pl.col("rule_id") == "D.3.9.6")
    print(f"D.3.9.6 Errors found: {d396_errs.height}")
    assert d396_errs.height == 0

    print("\nSUCCESS: All Contract Cascade consistency rules verified.")

if __name__ == "__main__":
    test_contract_cascades()
