import os
import sys
import polars as pl
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tower_kernel.services.workspace import WorkspaceService
from tower_kernel.services.diagnostic import DiagnosticService

MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
PGE_SUB_ZIP = "CSV_2025_Q1_6153783_1658789.ZIP"
PGE_ID = "6153783"
USER_ID = "raynier_test"
SESSION_ID = "session_001"

def test_pge_compliance_workflow():
    print(f"=== Starting TOWER-C Service Integration Test (PG&E - 4M Rows) ===")
    
    # 1. Workspace: Load Draft
    print("\n[1/3] WorkspaceService: Loading high-volume PG&E draft...")
    workspace_file = WorkspaceService.load_draft_submission(
        user_id=USER_ID,
        session_id=SESSION_ID,
        master_zip_path=MASTER_ZIP,
        sub_zip_name=PGE_SUB_ZIP
    )
    
    if not workspace_file or not os.path.exists(workspace_file):
        print("FAIL: Draft extraction failed.")
        return

    # 2. Diagnostic: Scorecard
    print("\n[2/3] DiagnosticService: Generating Compliance Scorecard...")
    scorecard = DiagnosticService.get_compliance_scorecard(workspace_file)
    
    print(f"Total Records Scanned: {scorecard['total_records']:,}")
    print("\nTop 5 Rules by Violation Count:")
    
    # Sort scorecard by error_count descending
    sorted_rules = sorted(scorecard["scorecard"], key=lambda x: x["error_count"], reverse=True)
    for rule in sorted_rules[:5]:
        print(f" - {rule['rule_id']}: {rule['error_count']:,} errors | {rule['description']}")

    # 3. Diagnostic: Evidence Drill-down
    print("\n[3/3] DiagnosticService: Drilling down into top rule violations...")
    top_rule_id = sorted_rules[0]["rule_id"] if sorted_rules else None
    if top_rule_id:
        evidence = DiagnosticService.get_rule_evidence(workspace_file, top_rule_id, limit=5)
        print(f"\nSample Evidence for Rule {top_rule_id}:")
        print(evidence.select(["transaction_unique_id", "source_row_index", "transaction_begin_date"]))

    # 4. Diagnostic: Export Report
    print("\n[BONUS] Exporting Audit Report...")
    report_path = DiagnosticService.export_compliance_report(workspace_file, PGE_ID, format="csv")
    print(f"Report location: {report_path}")

    # Cleanup (Optional for manual inspection, but good practice)
    # WorkspaceService.clear_workspace(USER_ID, SESSION_ID)
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_pge_compliance_workflow()
