import zipfile
import io
import os
import polars as pl
from pathlib import Path
from datetime import datetime
from tower_kernel.config import PATH_DISCOVERY_INDEX
from tower_kernel.utils.logging import log_progress

class MasterDiscoveryService:
    INDEX_PATH = PATH_DISCOVERY_INDEX
    HISTORIC_DIR = Path("tower_kernel/data/historic")

    @classmethod
    def rebuild_index(cls):
        """
        Performs a full deep-scan of all Master Quarterly archives to build an authoritative
        CID-to-TechnicalID mapping index.
        """
        log_progress("Starting Authoritative Master Discovery Scan...", "INFO")
        
        # Ensure registry directory exists
        cls.INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        all_mappings = []
        # Accept any case CSV_*.zip or csv_*.zip from the historic dir
        master_zips = sorted([
            p for p in cls.HISTORIC_DIR.glob("*.zip")
            if p.name.lower().startswith("csv_")
        ])
        
        if not master_zips:
            log_progress("No master archives found in historic directory.", "WARN")
            return

        for m_path in master_zips:
            log_progress(f"Scanning Master Archive: {m_path.name}")
            try:
                with zipfile.ZipFile(m_path, 'r') as m_zip:
                    inner_zips = [n for n in m_zip.namelist() if n.endswith(".ZIP")]
                    total_inner = len(inner_zips)
                    
                    for idx, inner_name in enumerate(inner_zips):
                        # Log progress every 500 items for better UX
                        if (idx + 1) % 500 == 0 or (idx + 1) == total_inner:
                            log_progress(f"        -> Scanning {m_path.name}: {idx + 1} of {total_inner} filings...")
                        try:
                            # 1. Extract technical_id from filename (invariant)
                            # Pattern: CSV_{YYYY}_Q{QQ}_{CID}_{TECHID}.ZIP
                            parts = inner_name.replace(".ZIP", "").split("_")
                            if len(parts) < 5:
                                continue
                            
                            tech_id = parts[-1]
                            
                            # 2. Authoritative Peek into ident.csv for CID verification
                            with m_zip.open(inner_name) as inner_f:
                                inner_zip_bytes = io.BytesIO(inner_f.read())
                                with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                                    ident_files = [n for n in z.namelist() if 'ident' in n.lower()]
                                    if not ident_files:
                                        continue
                                    
                                    with z.open(ident_files[0]) as id_f:
                                        # Use Polars to read just enough to get the CID
                                        df = pl.read_csv(id_f.read(), n_rows=1, ignore_errors=True)
                                        
                                        # Identify CID column (case-insensitive check for common FERC variants)
                                        cid_col = None
                                        for col in df.columns:
                                            if col.lower() in ['company_identifier', 'cid']:
                                                cid_col = col
                                                break
                                        
                                        if cid_col:
                                            cid = str(df.get_column(cid_col)[0]).strip()
                                            legal_name = str(df.get_column("company_name")[0]) if "company_name" in df.columns else "Unknown"
                                            
                                            all_mappings.append({
                                                "year": parts[1],
                                                "quarter": parts[2], # Already Q1, Q2 etc from the FERC filename parts
                                                "cid": cid,
                                                "technical_id": tech_id,
                                                "legal_name": legal_name,
                                                "source_zip": inner_name,
                                                "master_archive": m_path.name,
                                                "indexed_at": datetime.now()
                                            })
                        except Exception as e:
                            print(f"Skipping inner zip {inner_name} in {m_path.name}: {e}")
                            continue
            except Exception as e:
                log_progress(f"Error reading master archive {m_path.name}: {e}", "ERROR")

        if all_mappings:
            df_index = pl.DataFrame(all_mappings)
            # Ensure authoritative order (first match as agreed)
            df_index = df_index.unique(subset=["year", "quarter", "cid"], keep="first")
            df_index.write_parquet(cls.INDEX_PATH)
            log_progress(f"Discovery build COMPLETED. Registry Size: {len(all_mappings)} entries.", "SUCCESS")
        else:
            log_progress("Scan complete: No filings found to index.", "WARN")

    @classmethod
    def get_index_ldf(cls) -> pl.LazyFrame:
        """Returns the discovery index as a lazy frame if it exists."""
        if not cls.INDEX_PATH.exists():
            return pl.DataFrame(schema={
                "year": pl.String, "quarter": pl.String, "cid": pl.String, 
                "technical_id": pl.String, "legal_name": pl.String,
                "source_zip": pl.String, "master_archive": pl.String,
                "indexed_at": pl.Datetime
            }).lazy()
        return pl.scan_parquet(cls.INDEX_PATH)
