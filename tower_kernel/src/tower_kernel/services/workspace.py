import os
import shutil
import polars as pl
from pathlib import Path
from typing import List
from tower_kernel.ingest.streaming import stream_filing_to_polars, persist_to_lake, write_parquet_with_metadata

WORKSPACE_BASE = "data/workspace/drafts"

class WorkspaceService:
    @staticmethod
    def load_draft_submission(user_id: str, session_id: str, master_zip_path: str, sub_zip_name: str, company_id: str = "Unknown", company_name: str = "Unknown"):
        """
        Imports a specific filing into the user's transient workspace.
        This provides 'Compliance Parity' by using the exact same normalization 
        logic as the regulator's ingestion gate.
        """
        print(f"Loading draft for User: {user_id}, Session: {session_id}")
        
        # 1. Use the hardened streaming logic
        df = stream_filing_to_polars(master_zip_path, sub_zip_name)
        
        if df is not None:
            # Inject Traceability for the Filer
            df = df.with_row_index("source_row_index")
            df = df.with_columns(source_filename = pl.lit(sub_zip_name))
            
            # 2. Persist to Workspace Area (Draft Tier) with Identity Persistence
            workspace_path = Path(WORKSPACE_BASE) / f"user_id={user_id}" / f"session_id={session_id}"
            workspace_path.mkdir(parents=True, exist_ok=True)
            
            output_file = workspace_path / "draft_transactions.parquet"
            write_parquet_with_metadata(df, output_file, company_id, company_name)
            print(f"Draft persisted with metadata branding to: {output_file}")
            return str(output_file)
        
        return None

    @staticmethod
    def clear_workspace(user_id: str, session_id: str = None):
        """
        Cleans up transient draft data.
        """
        user_path = Path(WORKSPACE_BASE) / f"user_id={user_id}"
        if session_id:
            target = user_path / f"session_id={session_id}"
        else:
            target = user_path
            
        if target.exists():
            shutil.rmtree(target)
            print(f"Cleared workspace: {target}")
