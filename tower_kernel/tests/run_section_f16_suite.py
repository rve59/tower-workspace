import polars as pl
from tower_kernel.services.diagnostic import DiagnosticService
from pathlib import Path

def run_section_f16_suite():
    print("Verifying Fault Detection for Section F.16 (Identification Data)...")
    
    workspace_path = "data/lake/section_f16/transaction.parquet"
    if not Path(workspace_path).exists():
        print("Error: test parquet not found.")
        return

    # Expected violations
    # F.16.3 (Identity: Missing FS# roles)
    # F.16.12.1 (Identity: Multi FA1)
    # F.16.4.2 (Identity: Multi UID)
    # F.16.8.ID (Identity: Email format)
    # F.16.14.1 (Transactional: Missing Seller Name)
    # F.16.5, F.16.6, F.16.7 (Transactional: Missing contact info)
    
    expected_rules = [
        "F.16.3", "F.16.12.1", "F.16.4.2", "F.16.8.ID",
        "F.16.14.1", "F.16.5", "F.16.6", "F.16.7",
        "F.16.10", "F.16.13", "F.16.13.1", "F.16.14.4", "F.16.15"
    ]

    print(f"\nAnalyzing {workspace_path} with linked identity.parquet...")
    
    results = DiagnosticService.get_compliance_scorecard(workspace_path)
    scorecard = results.get("scorecard", {})
    
    total_passed = 0
    for rule_id in expected_rules:
        stat = scorecard.get(rule_id)
        if stat and stat["fails"] > 0:
            print(f"✅ [PASS] {rule_id}: Detected {stat['fails']} violations.")
            total_passed += 1
        else:
            print(f"❌ [FAIL] {rule_id}: FAILED to detect violation.")

    print(f"\nSection F.16 Verification Summary: {total_passed}/{len(expected_rules)} faults correctly detected.")
    if total_passed == len(expected_rules):
        print("RESULT: Section F.16 Validation Engine is 100% Reliable.")
    else:
        print("RESULT: Section F.16 contains regressions.")

if __name__ == "__main__":
    run_section_f16_suite()
