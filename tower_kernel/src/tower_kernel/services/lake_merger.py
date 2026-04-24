from pathlib import Path
import polars as pl
from tower_kernel.utils.logging import log_progress
from tower_kernel.ingest.schema_compiler import (
    TRANSACTION_COMPILER, 
    IDENT_COMPILER, 
    CONTRACT_COMPILER, 
    INDEX_COMPILER
)
from tower_kernel import config

class LakeMergerService:
    """
    Handles record-level updates (Upserts) and Greenfield Ingestion for the full EQR bundle.
    Supports Transactions, Identification, Contracts, and Index tables.
    """
    
    COMPILER_MAP = {
        "transactions": TRANSACTION_COMPILER,
        "ident": IDENT_COMPILER,
        "contracts": CONTRACT_COMPILER,
        "index": INDEX_COMPILER
    }

    FILE_MAP = {
        "transactions": config.TABLE_TRANSACTIONS,
        "ident": config.TABLE_IDENT,
        "contracts": config.TABLE_CONTRACTS,
        "index": config.TABLE_INDEX
    }

    @staticmethod
    def upsert_lake_table(cid: str, table_type: str, csv_path: str, year: str = None, quarter: str = None):
        """
        Generic entry point for infilrating any EQR table.
        Supports Deep Partitioning (Year/Quarter) and Greenfield Initialisation.
        """
        if table_type not in LakeMergerService.COMPILER_MAP:
            log_progress(f"Unsupported table type: {table_type}", "ERROR")
            return {"error": f"Unsupported table: {table_type}"}

        compiler = LakeMergerService.COMPILER_MAP[table_type]
        table_file = LakeMergerService.FILE_MAP[table_type]
        
        # 1. Resolve Partition Path
        lake_dir = config.get_tier_path(cid, config.TIER_BRONZE, year=year, quarter=quarter)
        master_path = lake_dir / table_file
        
        log_progress(f"Infiltrating {table_type} for CID: {cid} | Period: {year or 'ALL'} {quarter or ''}")
        
        # 2. Load Existing Data (if any)
        master_df = None
        initial_count = 0
        if master_path.exists():
            log_progress(f"Loading existing {table_type} partition...")
            master_df = pl.read_parquet(master_path)
            initial_count = master_df.height
        else:
            log_progress(f"Greenfield mode: Initializing new {table_type} partition.", "INFO")

        # 3. Load and Normalize Incoming Data
        log_progress(f"Parsing source file: {Path(csv_path).name}")
        try:
            # Load with Bronze string-first schema
            raw_df = pl.read_csv(csv_path, schema_overrides=compiler["schema"], ignore_errors=True)
            
            # Robust Renaming (Handling case-insensitive / space-insensitive headers)
            actual_cols = raw_df.columns
            rename_map = compiler["model"].__class__.get_robust_rename_map(compiler["model"], actual_cols) if hasattr(compiler["model"], "__class__") and hasattr(compiler["model"].__class__, "get_robust_rename_map") else compiler["rename"]
            
            # Fallback to standard rename if robust one isn't available on singleton
            # Actually, SchemaCompiler has the methods. Let's use the compiler's rename map for now.
            available_map = {k: v for k, v in compiler["rename"].items() if k in raw_df.columns}
            incoming_df = raw_df.rename(available_map)
            
            # Add context metadata
            new_cols = [
                pl.lit("INFILTRATION").alias("filing_type"),
                pl.lit(Path(csv_path).name).alias("source_filename"),
                pl.arange(0, pl.len()).alias("source_row_index")
            ]
            
            # Context Injection (Year/Quarter from folder path)
            if year and "filing_year" not in incoming_df.columns:
                new_cols.append(pl.lit(str(year)).alias("filing_year"))
            if quarter and "filing_quarter" not in incoming_df.columns:
                q_val = str(quarter).replace("Q", "")
                new_cols.append(pl.lit(q_val).alias("filing_quarter"))
                
            incoming_df = incoming_df.with_columns(new_cols)

        except Exception as e:
            log_progress(f"Failed to parse ingestion CSV: {e}", "ERROR")
            return {"error": f"Parse error: {e}"}

        # 4. Merge Logic
        if master_df is not None:
            log_progress("Executing identity-aware merge...")
            
            # Align schema with master
            aligned_exprs = []
            for col_name in master_df.columns:
                target_dtype = master_df.schema[col_name]
                if col_name in incoming_df.columns:
                    aligned_exprs.append(pl.col(col_name).cast(target_dtype))
                else:
                    aligned_exprs.append(pl.lit(None).cast(target_dtype).alias(col_name))
            
            incoming_df = incoming_df.select(aligned_exprs)
            merged_df = pl.concat([master_df, incoming_df])
            
            # Deduplication logic depends on table type
            # Transactions use source_filename + transaction_unique_id
            # Identity/Contracts might use different keys, but for now we follow the same 'latest record wins' rule
            # per (source_filename, UID) for Transactions, and (UID) for others might be better?
            # Actually, keeping source_filename in the key allows multi-file sources to coexist
            
            dedup_keys = ["source_filename"]
            if "transaction_unique_id" in merged_df.columns:
                dedup_keys.append("transaction_unique_id")
            elif "contract_unique_id" in merged_df.columns:
                dedup_keys.append("contract_unique_id")
            elif "seller_company_name" in merged_df.columns: # Ident fallback
                dedup_keys.append("seller_company_name")
            
            final_df = merged_df.unique(subset=dedup_keys, keep="last")
        else:
            # Initialization
            final_df = incoming_df

        final_count = final_df.height
        overwritten_count = (initial_count + incoming_df.height) - final_count

        log_progress(f"Infiltration complete: {incoming_df.height} records processed.")
        
        # 5. Write back
        final_df.write_parquet(master_path)
        log_progress(f"Bronze Lake updated: {master_path.relative_to(config.PACKAGE_ROOT)}", "SUCCESS")
        
        return {
            "status": "success",
            "table": table_type,
            "path": str(master_path),
            "processed": incoming_df.height,
            "overwritten": overwritten_count,
            "new": incoming_df.height - overwritten_count
        }

    @staticmethod
    def upsert_transactions(cid: str, correction_csv_path: str):
        """
        Legacy/Convenience wrapper for backward compatibility.
        """
        return LakeMergerService.upsert_lake_table(cid, "transactions", correction_csv_path)
