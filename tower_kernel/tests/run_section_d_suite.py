import polars as pl
from tower_kernel.services.diagnostic import DiagnosticService
from pathlib import Path

def run_section_d_suite():
    print("Verifying Fault Detection for Section D (Structural Integrity)...")
    
    test_dir = Path("data/lake/section_d")
    scenarios = [
        ("D_SECTION_NEW.parquet", ["D.3.9.1", "D.3.1.2"]),
        ("D_SECTION_REPLACE.parquet", ["D.3.9.2"]),
        ("D_SECTION_DELETE.parquet", ["D.3.9.3", "D.3.9.9"]),
        ("D_SECTION_CONTRACT_NEW.parquet", ["D.3.9.6"]),
        ("D_SECTION_CONTRACT_DELETE.parquet", ["D.3.9.8"]),
    ]

    total_passed = 0
    total_checks = 0

    for filename, expected_rules in scenarios:
        path = test_dir / filename
        print(f"\nAnalyzing {filename}...")
        
        results = DiagnosticService.get_compliance_scorecard(str(path))
        scorecard = results.get("scorecard", {})
        
        for rule_id in expected_rules:
            total_checks += 1
            stat = scorecard.get(rule_id)
            if stat and stat["fails"] > 0:
                print(f"✅ [PASS] {rule_id}: Detected {stat['fails']} violations.")
                total_passed += 1
            else:
                print(f"❌ [FAIL] {rule_id}: FAILED to detect violation.")

    print(f"\nSection D Verification Summary: {total_passed}/{total_checks} faults correctly detected.")
    if total_passed == total_checks:
        print("RESULT: Section D Validation Engine is 100% Reliable.")
    else:
        print("RESULT: Section D contains regressions.")

if __name__ == "__main__":
    run_section_d_suite()
