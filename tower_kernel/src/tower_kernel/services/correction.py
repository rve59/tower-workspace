import polars as pl
import datetime
import re
from pathlib import Path
from tower_kernel import config
from tower_kernel.services.lake_merger import LakeMergerService
from tower_kernel.utils.logging import log_progress

class CorrectionService:
    """
    Handles the generation of manual correction templates and the automated scanning 
    of company inboxes for surgical record updates and Greenfield Infiltration.
    """

    @staticmethod
    def export_correction_templates(cid: str):
        """
        Scans the latest compliance summary and exports individual CSV templates 
        per Rule ID for records that failed validation.
        """
        reports_dir = config.get_tier_path(cid, config.TIER_REPORTS)
        bronze_dir = config.get_tier_path(cid, config.TIER_BRONZE)
        
        # 1. Find latest compliance summary
        summary_files = sorted(list(reports_dir.glob("compliance_summary_*.parquet")))
        if not summary_files:
            log_progress(f"No compliance reports found for {cid}. Run validation first.", "ERROR")
            return False
            
        latest_report = summary_files[-1]
        log_progress(f"Loading latest failure report: {latest_report.name}")
        errors_df = pl.read_parquet(latest_report)
        
        if errors_df.height == 0:
            log_progress("No failures found to export. Data is clean.", "SUCCESS")
            return True

        # 2. Load Bronze Master (Wide)
        master_path = bronze_dir / config.TABLE_TRANSACTIONS
        if not master_path.exists():
            log_progress("Bronze master lake missing.", "ERROR")
            return False
            
        log_progress("Joining failure log with master lake to build templates...")
        master_ldf = pl.scan_parquet(master_path)
        
        # 3. Create per-rule exports
        rules = errors_df["rule_id"].unique().to_list()
        
        for rule_id in rules:
            rule_errors = errors_df.filter(pl.col("rule_id") == rule_id)
            
            template_ldf = master_ldf.join(
                rule_errors.lazy(),
                on=["source_filename", "transaction_unique_id"],
                how="inner"
            )
            
            output_path = reports_dir / f"{rule_id}_remediation_template.csv"
            template_df = template_ldf.collect()
            template_df.write_csv(output_path)
            log_progress(f"Exported {template_df.height} records for {rule_id} -> {output_path.name}")
            
        return True

    @staticmethod
    def process_inbox(cid: str):
        """
        Recursively scans the company's inbox directory.
        Identifies table types via filename tags and extracts context (Y/Q) from folder structure.
        Supports Transactions, Identification, Contracts, and Index bundles.
        """
        inbox_dir = config.get_tier_path(cid, config.TIER_INBOX)
        
        # Recursive walk to support /2024/Q3/ style bundles
        csv_files = list(inbox_dir.rglob("*.csv"))
        if not csv_files:
            log_progress(f"Inbox empty for {cid}.", "INFO")
            return {"processed": 0}
            
        results = []
        for csv_path in csv_files:
            # 1. Detect Table Type from filename tags
            table_type = CorrectionService._detect_table_type(csv_path.name)
            if not table_type:
                log_progress(f"Skipping unidentified file: {csv_path.name}. (Expected tags: ident, contract, transaction, index)", "WARNING")
                continue

            # 2. Extract Context (Year/Quarter) from folder structure
            year, quarter = CorrectionService._extract_context(csv_path, inbox_dir)
            
            log_progress(f"Processing infiltration: {csv_path.relative_to(inbox_dir)} -> {table_type.upper()}")
            
            # 3. Dispatch to Generic Infiltration Engine
            res = LakeMergerService.upsert_lake_table(
                cid=cid, 
                table_type=table_type, 
                csv_path=str(csv_path),
                year=year,
                quarter=quarter
            )
            
            results.append({
                "file": str(csv_path.relative_to(inbox_dir)),
                "table": table_type,
                "status": res.get("status", "error"),
                "period": f"{year or ''} {quarter or ''}".strip(),
                "processed": res.get("processed", 0)
            })
            
        return {
            "total_files": len(csv_files),
            "results": results
        }

    @staticmethod
    def _detect_table_type(filename: str) -> str:
        """
        Uses filename tags to determine which EQR table the CSV belongs to.
        """
        fn = filename.lower()
        if "ident" in fn: return "ident"
        if "contract" in fn: return "contracts"
        if "transaction" in fn: return "transactions"
        if "index" in fn: return "index"
        return None

    @staticmethod
    def _extract_context(file_path: Path, root_inbox: Path):
        """
        Parses the relative path to extract Year and Quarter.
        Supports formats like: root/2024/Q3/file.csv or root/2024/3/file.csv
        """
        try:
            rel_path = file_path.relative_to(root_inbox)
            parts = rel_path.parts[:-1] # Exclude the file name
            
            year = None
            quarter = None
            
            for part in parts:
                # Year check (4 digits)
                if re.match(r"^\d{4}$", part):
                    year = part
                # Quarter check (Q1-Q4 or 1-4)
                if re.match(r"^[Qq]?[1-4]$", part):
                    quarter = part.upper()
                    if not quarter.startswith("Q"):
                        quarter = f"Q{quarter}"
                        
            return year, quarter
        except Exception:
            return None, None
