import os
import sys
import polars as pl
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tower_kernel.services.diagnostic import DiagnosticService

WORKSPACE_PGE = "data/workspace/drafts/user_id=raynier_test/session_id=session_001/draft_transactions.parquet"

def test_ai_audit_exit():
    print(f"=== Starting TOWER-S AI Audit Integration Test (Cluster Analysis) ===")
    
    if not os.path.exists(WORKSPACE_PGE):
        print("FAIL: Workspace missing. Run tests/test_services.py first.")
        return

    # Trigger targeted AI analysis for Rule F.25.20 (The CAISO Cluster)
    print("\nTriggering AI Deep-Dive for F.25.20 (858K violating records)...")
    
    analysis = DiagnosticService.analyze_failure_set_with_ai(WORKSPACE_PGE, "F.25.20")
    
    if "error" in analysis:
        print(f"FAIL: {analysis['error']}")
        return

    print("\n[AI ANALYSIS RESULT]")
    print(f"Rule: {analysis['rule_id']}")
    print(f"Diagnosis: {analysis['diagnosis']}")
    print(f"\nRemediation Strategy:\n{analysis['remediation_strategy']}")
    print(f"\nConfidence: {analysis['confidence_score'] * 100}%")

    # Verify Cluster Sampling (Internal logging)
    print("\nTest Complete.")

if __name__ == "__main__":
    test_ai_audit_exit()
