import polars as pl
from tower_kernel.services.diagnostic import DiagnosticService
from pathlib import Path

def run_section_f17_suite():
    print("Verifying Fault Detection for Section F.17 (Semantic & Product Consistency)...")
    
    workspace_path = "data/lake/section_f17/transaction.parquet"
    if not Path(workspace_path).exists():
        print("Error: test parquet not found.")
        return

    expected_rules = [
        "F.17.1", "F.17.3", "F.17.7", "F.17.13",
        "F.17.11.1", "F.17.20"
    ]

    print(f"\nAnalyzing {workspace_path} with linked contract.parquet...")
    
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

    print(f"\nSection F.17 Verification Summary: {total_passed}/{len(expected_rules)} faults correctly detected.")
    if total_passed == len(expected_rules):
        print("RESULT: Section F.17 Validation Engine is 100% Reliable.")
    else:
        print("RESULT: Section F.17 contains regressions.")

if __name__ == "__main__":
    run_section_f17_suite()
