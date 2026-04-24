import json
import datetime
import shutil
from pathlib import Path
from tower_kernel import config
from tower_kernel.utils.logging import log_progress

class PromotionService:
    """
    Handles the manual promotion of data from Bronze to Silver after human audit.
    Maintains a standalone audit log for each company.
    """

    @staticmethod
    def promote_to_silver(cid: str, auditor_name: str = "TOWER_USER") -> bool:
        """
        Explicitly promotes the current Bronze datasets to the Silver tier.
        Records the event in a dedicated audit_log.json file.
        """
        if not cid:
            log_progress("Promotion failed: Missing Company ID.", "ERROR")
            return False
        
        bronze_dir = config.get_tier_path(cid, config.TIER_BRONZE)
        silver_dir = config.get_tier_path(cid, config.TIER_SILVER)
        
        log_progress(f"Initiating Promotion to SILVER for CID: {cid}")
        
        try:
            # 1. Verification: Ensure Bronze data actually exists
            tables = [
                config.TABLE_TRANSACTIONS, 
                config.TABLE_IDENT, 
                config.TABLE_CONTRACTS, 
                config.TABLE_INDEX
            ]
            
            existing_tables = []
            for table in tables:
                src = bronze_dir / table
                if src.exists():
                    existing_tables.append(table)
            
            if not existing_tables:
                log_progress(f"Promotion failed: No Bronze data found for {cid}.", "ERROR")
                return False

            # 2. Perform File Migration (Copy)
            for table in existing_tables:
                src = bronze_dir / table
                dst = silver_dir / table
                shutil.copy2(src, dst)
                log_progress(f"Promoted: {table}")

            # 3. Update Audit Log
            PromotionService._record_audit_event(cid, "PROMOTION_TO_SILVER", {
                "auditor": auditor_name,
                "tables_promoted": existing_tables,
                "source_tier": config.TIER_BRONZE,
                "target_tier": config.TIER_SILVER
            })
            
            log_progress(f"Promotion Successful: {cid} moved to SILVER.", "SUCCESS")
            return True
            
        except Exception as e:
            log_progress(f"Promotion Failed for {cid}: {e}", "ERROR")
            return False

    @staticmethod
    def _record_audit_event(cid: str, event_type: str, details: dict):
        """
        Writes a timestamped entry to the company's standalone audit_log.json.
        """
        # Audit log lives in the CID root folder
        audit_log_path = config.LAKE_ROOT / str(cid) / "audit_log.json"
        
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        log_entries = []
        if audit_log_path.exists():
            try:
                with open(audit_log_path, "r") as f:
                    log_entries = json.load(f)
            except Exception:
                log_entries = []
                
        log_entries.append(event)
        
        with open(audit_log_path, "w") as f:
            json.dump(log_entries, f, indent=4)
            
        log_progress(f"Audit log updated: {audit_log_path.name}")
