import polars as pl
from tower_kernel.services.diagnostic import DiagnosticService
from pathlib import Path
import json

def run_test_suite():
    print("Running TOWER-C Compliance Validation Suite...")
    
    test_parquet = "data/lake/TEST_COMPLIANCE_180.parquet"
    if not Path(test_parquet).exists():
        print(f"Error: {test_parquet} not found. Run the generator first.")
        return

    # Invoke the kernel validation engine
    scorecard_results = DiagnosticService.get_compliance_scorecard(test_parquet)
    
    # We expect failures for specific rules
    # Note: scorecard_results['scorecard'] maps rule_id -> {fails, total, category}
    scorecard = scorecard_results.get("scorecard", {})
    
    expected_rules = [
        "F.24.1", "F.25.2.1", "F.23.5", "F.24.6", "F.24.3", "F.17.8.1", "F.21.5",
        "F.25.2.2", "F.25.2.5", "F.22.3", "F.16.8", "D.3.9.1"
    ]
    
    print("\n--- Compliance Assertion Report ---")
    passed_count = 0
    for rule_id in expected_rules:
        stat = scorecard.get(rule_id)
        if stat and stat["fails"] > 0:
            print(f"✅ [PASS] Rule {rule_id}: Detected {stat['fails']} violations.")
            passed_count += 1
        else:
            print(f"❌ [FAIL] Rule {rule_id}: No violations detected.")

    print(f"\nSummary: {passed_count}/{len(expected_rules)} rules verified.")
    
    if passed_count == len(expected_rules):
        print("\nCOMPLIANCE SUITE SUCCESS: Kernel is accurately detecting intentional violations.")
    else:
        print("\nCOMPLIANCE SUITE INCOMPLETE: Some rules are not triggering as expected.")

if __name__ == "__main__":
    run_test_suite()
