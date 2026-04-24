import polars as pl
from pathlib import Path
import zipfile
import uuid
import os
import io
from datetime import datetime
from tower_kernel.services.registry_mirror import RegistryMirrorService
from tower_kernel.services.discovery_indexer import MasterDiscoveryService
from tower_kernel.ingest.schema_compiler import (
    SchemaCompiler, IDENT_COMPILER, CONTRACT_COMPILER, TRANSACTION_COMPILER, INDEX_COMPILER
)
from tower_kernel.utils.logging import log_progress
import tower_kernel.config as config

class FERCMasterExtractor:
    # Manual overrides for Ident files which often use different vocab than the data models
    IDENT_OVERRIDE_MAP = {
        "company_name": "seller_name",
        "company_identifier": "seller_cid",
        "contact_name": "seller_contact",
        "contact_phone": "seller_contact_phone",
        "contact_email": "seller_contact_email",
        "filing_quarter": "filing_quarter",
        "filing_year": "filing_year"
    }

    """
    Extracts a specific company's EQR filing datasets from the FERC historical master directories.
    Target: data/historic/CSV_{YYYY}_Q{Q}.zip
    """
    def __init__(self, year, quarter, cid: str):
        self.year = str(year)
        # Normalize quarter: Strip 'Q' if present, then ensure it's prefixed for consistency
        q_clean = str(quarter).upper().replace("Q", "")
        self.quarter = f"Q{q_clean}"
        self.cid = cid
        # Use restructured path: CID / YYYY-QQ / bronze
        self.lake_dir = config.get_tier_path(cid, config.TIER_BRONZE, self.year, self.quarter)

    def _get_technical_id(self, index_ldf: pl.LazyFrame) -> str:
        res = index_ldf.filter(
            (pl.col("year") == str(self.year)) & 
            (pl.col("quarter") == str(self.quarter)) & 
            (pl.col("cid") == self.cid)
        ).collect()
        
        if res.height == 0:
            return "0"
        
        tech_id = res.get_column("technical_id")[0]
        return tech_id or "0"

    def _robust_rename(self, df, compiler_dict, is_ident=False):
        mapping = SchemaCompiler.get_robust_rename_map(compiler_dict["model"], df.columns)
        
        if is_ident:
            # Apply identity-specific overrides for commonly found registry headers
            for k, v in self.IDENT_OVERRIDE_MAP.items():
                if k in df.columns:
                    mapping[k] = v

        return df.rename(mapping)

    def extract(self):
        start_time = datetime.now()
        total_records = 0
        legal_name = "Unknown Company"
        log_progress(f"Ingesting company's zip file for the {self.year}-{self.quarter} into the kernel")
        
        # 1. Open the Master Quarterly ZIP (e.g. CSV_2025_Q1.zip)
        historic_dir = Path("tower_kernel/data/historic")
        # Fix: self.quarter already has the 'Q', so don't double it in the format string
        master_zip_path = historic_dir / f"CSV_{self.year}_{self.quarter}.zip"
        
        if not master_zip_path.exists():
            # Robust fallback: case-insensitive match for CSV_{year}_{quarter}.zip
            pattern = f"csv_{self.year}_{self.quarter}.zip"
            matches = [p for p in historic_dir.glob("*.zip") if p.name.lower() == pattern.lower()]
            if matches:
                master_zip_path = matches[0]
                log_progress(f"Resolved master archive via case-insensitive match: {master_zip_path.name}")
            else:
                log_progress(f"Master archive missing: {master_zip_path}", "ERROR")
                raise FileNotFoundError(f"Master source not found: {master_zip_path}")

        # 2. Discover authoritative filing: Try Index first, Fallback to sequential scan
        inner_zip_name = None
        
        # Attempt index lookup (Authoritative & Fast)
        index_ldf = MasterDiscoveryService.get_index_ldf()
        match = index_ldf.filter(
            (pl.col("year") == str(self.year)) & 
            (pl.col("quarter") == str(self.quarter)) & 
            (pl.col("cid") == self.cid)
        ).collect()

        if match.height > 0:
            inner_zip_name = match.get_column("source_zip")[0]
            log_progress(f"Resolved authoritative filing via index: {inner_zip_name}")
        else:
            log_progress(f"CID {self.cid} not in index. Falling back to archive scan...", "WARN")
            with zipfile.ZipFile(master_zip_path, 'r') as m_zip:
                pattern_fragment = f"CSV_{self.year}_Q{self.quarter}_{self.cid}_"
                for name in m_zip.namelist():
                    if name.startswith(pattern_fragment) and name.endswith(".ZIP"):
                        inner_zip_name = name
                        break
        
        if not inner_zip_name:
            log_progress(f"No filing found for CID {self.cid} in {master_zip_path.name}", "ERROR")
            raise FileNotFoundError(f"CID {self.cid} not found in master archive.")

        with zipfile.ZipFile(master_zip_path, 'r') as m_zip:
            # 3. Extract the inner filing ZIP (process in-memory)
            with m_zip.open(inner_zip_name) as inner_f:
                inner_zip_bytes = io.BytesIO(inner_f.read())
                with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                    files = z.namelist()
                    
                    def get_internal_csv(hint):
                        for f in files:
                            if hint in f.lower() and f.endswith(".CSV"):
                                return f
                        return None
                    
                    ident_file = get_internal_csv("ident")
                    contracts_file = get_internal_csv("contracts")
                    tx_file = get_internal_csv("transaction")
                    index_file = get_internal_csv("index")
                    
                    # 4. Process Identification
                    if ident_file:
                        log_progress(f"Infiltrating Identity: {ident_file}")
                        with z.open(ident_file) as f:
                            ident_raw = pl.read_csv(f.read(), schema_overrides=IDENT_COMPILER["schema"], ignore_errors=True)
                            total_records += ident_raw.height
                            
                            ident_final = self._robust_rename(ident_raw, IDENT_COMPILER, is_ident=True)
                            
                            # Capture Legal Name for telemetry
                            if ident_final.height > 0 and "seller_name" in ident_final.columns:
                                legal_name = ident_final.get_column("seller_name")[0]

                            ident_final.write_parquet(self.lake_dir / config.TABLE_IDENT)

                    # 5. Process Contracts
                    if contracts_file:
                        log_progress(f"Infiltrating Contracts: {contracts_file}")
                        with z.open(contracts_file) as f:
                            contracts_raw = pl.read_csv(f.read(), schema_overrides=CONTRACT_COMPILER["schema"], ignore_errors=True)
                            total_records += contracts_raw.height
                            contracts_final = self._robust_rename(contracts_raw, CONTRACT_COMPILER)
                            contracts_final.write_parquet(self.lake_dir / config.TABLE_CONTRACTS)

                    # 6. Process Transactions
                    if tx_file:
                        log_progress(f"Infiltrating Transactions: {tx_file}")
                        with z.open(tx_file) as f:
                            tx_raw = pl.read_csv(f.read(), schema_overrides=TRANSACTION_COMPILER["schema"], ignore_errors=True)
                            total_records += tx_raw.height
                            tx_final = self._robust_rename(tx_raw, TRANSACTION_COMPILER)
                            
                            # Add synthetic enrichment (Metadata preserved for audit)
                            tx_final = tx_final.with_columns([
                                pl.lit("NEW").alias("filing_type"),
                                pl.lit(inner_zip_name).alias("source_filename"),
                                pl.arange(0, pl.len()).alias("source_row_index")
                            ])
                            tx_final.write_parquet(self.lake_dir / config.TABLE_TRANSACTIONS)

                    # 7. Process Public Index
                    if index_file:
                        log_progress(f"Infiltrating Public Index: {index_file}")
                        with z.open(index_file) as f:
                            index_raw = pl.read_csv(f.read(), schema_overrides=INDEX_COMPILER["schema"], ignore_errors=True)
                            total_records += index_raw.height
                            index_final = self._robust_rename(index_raw, INDEX_COMPILER)
                            index_final.write_parquet(self.lake_dir / config.TABLE_INDEX)
                        
        elapsed = (datetime.now() - start_time).total_seconds()
        log_progress(f"Infiltration COMPLETE. {legal_name} ({self.cid}): {total_records:_} records in {elapsed:.2f}s.", "SUCCESS")
