import polars as pl
from pathlib import Path
import json
import shutil
from tower_kernel import config
from tower_kernel.services.diagnostic import DiagnosticService
from tower_kernel.services.correction import CorrectionService
from tower_kernel.services.promotion import PromotionService
from tower_kernel.services.lake_merger import LakeMergerService
from tower_kernel.utils.logging import log_progress

def run_remediation_cycle_test():
    cid = "TEST_REMEDIATION_CORP"
    log_progress(f"Starting Full Remediation Cycle Test for {cid}")

    # 0. Setup Clean Workspace
    cid_dir = config.LAKE_ROOT / cid
    if cid_dir.exists():
        shutil.rmtree(cid_dir)
        
    bronze_dir = config.get_tier_path(cid, config.TIER_BRONZE)
    reports_dir = config.get_tier_path(cid, config.TIER_REPORTS)
    inbox_dir = config.get_tier_path(cid, config.TIER_INBOX)

    # 1. Simulate 'Bad' Data in Bronze
    # We'll create a simple transactions.parquet with one record that has a known failure
    # (e.g. failing a price rule if we have one, or just a placeholder)
    
    bad_data = pl.DataFrame({
        "source_filename": ["initial_filing.csv"],
        "transaction_unique_id": ["TX_001"],
        "price": ["-100.0"], # Should fail a 'Positive Price' rule (V4.TYPE.price)
        "quantity": ["50.0"],
        "product_name": ["ENERGY"],
        "customer_company_name": ["Buyer A"],
        "rate_units": ["MWH"],
        "filing_year": ["2024"],
        "filing_quarter": ["1"]
    })
    
    master_path = bronze_dir / config.TABLE_TRANSACTIONS
    bad_data.write_parquet(master_path)
    log_progress("Injected 'bad' record into Bronze Lake.")

    # 2. Run Validation & Export Templates
    # Note: DiagnosticService.get_compliance_scorecard actually runs the validation
    scorecard = DiagnosticService.get_compliance_scorecard(str(master_path))
    log_progress(f"Scorecard generated. Total records: {scorecard['total_records']}")
    
    # Export summary report (internal)
    DiagnosticService.export_compliance_report(str(master_path), cid, format="parquet")
    
    # Export user correction templates (per-rule)
    CorrectionService.export_correction_templates(cid)
    
    # Verify templates exist
    templates = list(reports_dir.glob("*_remediation_template.csv"))
    log_progress(f"Found {len(templates)} correction templates in reports directory.")
    assert len(templates) > 0, "No templates exported!"

    # 3. Simulate User Correction
    # We'll take the first template, fix the price, and drop it in the inbox
    first_template = templates[0]
    correction_df = pl.read_csv(first_template)
    
    # Fix the price: -100 -> +500
    correction_df = correction_df.with_columns(pl.lit(500.0).alias("price"))
    
    corrected_file_path = inbox_dir / "user_fix_TX001.csv"
    correction_df.write_csv(corrected_file_path)
    log_progress(f"Sideloaded corrected record into inbox: {corrected_file_path.name}")

    # 4. Process Inbox
    process_res = CorrectionService.process_inbox(cid)
    log_progress(f"Inbox processing complete: {process_res['total_files']} files handled.")

    # 5. Verify Repair in Bronze
    repaired_df = pl.read_parquet(master_path)
    final_price = float(repaired_df.filter(pl.col("transaction_unique_id") == "TX_001")["price"][0])
    log_progress(f"Verified Price in Bronze Lake for TX_001: {final_price}")
    assert final_price == 500.0, f"Repair failed! Price is {final_price}"

    # 6. Manual Promotion
    PromotionService.promote_to_silver(cid, auditor_name="AUDITOR_JOE")
    
    # 7. Final Verification
    silver_path = config.get_tier_path(cid, config.TIER_SILVER) / config.TABLE_TRANSACTIONS
    assert silver_path.exists(), "Silver Lake missing transactions.parquet!"
    
    audit_log_path = config.LAKE_ROOT / cid / "audit_log.json"
    assert audit_log_path.exists(), "Audit log missing!"
    
    with open(audit_log_path, "r") as f:
        audit_data = json.load(f)
        log_progress(f"Last Audit Event: {audit_data[-1]['event_type']} by {audit_data[-1]['details']['auditor']}")
        assert audit_data[-1]["details"]["auditor"] == "AUDITOR_JOE"

    log_progress("FULL REMEDIATION CYCLE TEST PASSED!", "SUCCESS")

if __name__ == "__main__":
    run_remediation_cycle_test()
