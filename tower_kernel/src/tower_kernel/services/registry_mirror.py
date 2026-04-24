import polars as pl
import os
import io
import json
import urllib.request
from datetime import datetime
from tower_kernel.config import PATH_CID_MASTER, PATH_CID_METADATA
from tower_kernel.utils.logging import log_progress

class RegistryMirrorService:
    REGISTRY_PATH = PATH_CID_MASTER
    METADATA_PATH = PATH_CID_METADATA
    OFFICIAL_URL = "https://data.ferc.gov/api/v1/dataset/26/export/?format=csv"
    
    REGISTRY_SCHEMA = {
        "cid": pl.String,
        "technical_id": pl.String,
        "legal_name": pl.String,
        "program": pl.String,
        "website": pl.String,
        "address": pl.String,
        "address2": pl.String,
        "city": pl.String,
        "state": pl.String,
        "zip": pl.String,
        "effective_start_date": pl.Date,
        "effective_end_date": pl.Date
    }

    @classmethod
    def import_registry(cls, csv_path: str):
        """
        Imports a CID registry CSV and merges it into the local Parquet mirror.
        Maps the User's new multi-column format to the internal schema.
        """
        if not os.path.exists(csv_path):
            log_progress(f"ERROR: Local registry CSV not found at {csv_path}", "ERROR")
            return

        try:
            log_progress(f"Ingesting multi-column registry: {os.path.basename(csv_path)}")
            df = pl.read_csv(csv_path)
            
            # Map columns to internal schema
            mapping = {
                "CID": "cid",
                "Organization_Name": "legal_name",
                "Program": "program",
                "Company_Website": "website",
                "Address": "address",
                "Address2": "address2",
                "City": "city",
                "State": "state",
                "Zip": "zip"
            }
            
            # Filter and rename
            available_cols = [c for c in mapping.keys() if c in df.columns]
            new_data = df.select(available_cols).rename({c: mapping[c] for c in available_cols if c in mapping})
            
            # Ensure technical_id and dates exist
            if "technical_id" not in new_data.columns:
                new_data = new_data.with_columns(pl.lit("0").alias("technical_id"))
            
            # Add default dates for manual registry entries
            if "effective_start_date" not in new_data.columns:
                new_data = new_data.with_columns(pl.lit("1900-01-01").str.to_date("%Y-%m-%d").alias("effective_start_date"))
            if "effective_end_date" not in new_data.columns:
                new_data = new_data.with_columns(pl.lit(None).cast(pl.Date).alias("effective_end_date"))

            # Standardize logic: apply schema to new_data
            for col_name, dtype in cls.REGISTRY_SCHEMA.items():
                if col_name not in new_data.columns:
                    new_data = new_data.with_columns(pl.lit(None).cast(dtype).alias(col_name))
                else:
                    new_data = new_data.with_columns(pl.col(col_name).cast(dtype, strict=False))

            if os.path.exists(cls.REGISTRY_PATH):
                existing = pl.read_parquet(cls.REGISTRY_PATH)
                
                # Migrate existing data to new schema and types
                for col_name, dtype in cls.REGISTRY_SCHEMA.items():
                    if col_name not in existing.columns:
                        existing = existing.with_columns(pl.lit(None).cast(dtype).alias(col_name))
                    else:
                        existing = existing.with_columns(pl.col(col_name).cast(dtype, strict=False))
                
                # Align column orders
                col_names = list(cls.REGISTRY_SCHEMA.keys())
                existing = existing.select(col_names)
                new_data = new_data.select(col_names)
                
                # Merge: Prefer the new CSV data for the same CID
                merged = pl.concat([existing, new_data]).unique(subset=["cid", "legal_name"], keep="last")
            else:
                merged = new_data

            os.makedirs(os.path.dirname(cls.REGISTRY_PATH), exist_ok=True)
            merged.write_parquet(cls.REGISTRY_PATH)
            cls._update_last_synced()
            log_progress(f"SUCCESS: Registry aligned with {merged.height} records.", "SUCCESS")
        except Exception as e:
            log_progress(f"ERROR: Registry alignment failed: {e}", "ERROR")

    @classmethod
    def get_mirror_ldf(cls) -> pl.LazyFrame:
        """Returns the local registry mirror with the expanded schema."""
        if not os.path.exists(cls.REGISTRY_PATH):
            return pl.DataFrame(schema=cls.REGISTRY_SCHEMA).lazy()
        return pl.scan_parquet(cls.REGISTRY_PATH)

    @classmethod
    def bootstrap_sample_data(cls):
        """Initializes with major utilities in the new schema."""
        sample_data = pl.DataFrame([
            {"cid": "6153783", "technical_id": "89341", "legal_name": "Pacific Gas and Electric Company", "program": "FPA", "effective_start_date": "1905-10-10"},
            {"cid": "C000722", "technical_id": "42112", "legal_name": "California Independent System Operator", "program": "FERC-ISO", "effective_start_date": "1998-03-31"},
            {"cid": "C000572", "technical_id": "99318", "legal_name": "PJM Interconnection", "program": "FERC-ISO", "effective_start_date": "1927-09-26"}
        ]).with_columns([
            pl.col("effective_start_date").str.to_date("%Y-%m-%d"),
            pl.lit(None).cast(pl.Date).alias("effective_end_date"),
            pl.lit(None).cast(pl.String).alias("website"),
            pl.lit(None).cast(pl.String).alias("address"),
            pl.lit(None).cast(pl.String).alias("address2"),
            pl.lit(None).cast(pl.String).alias("city"),
            pl.lit(None).cast(pl.String).alias("state"),
            pl.lit(None).cast(pl.String).alias("zip")
        ])
        
        os.makedirs(os.path.dirname(cls.REGISTRY_PATH), exist_ok=True)
        sample_data.write_parquet(cls.REGISTRY_PATH)

    @classmethod
    def sync_official_registry(cls):
        """Fetches from FERC API and projects onto the new aligned schema."""
        log_progress(f"[STD-API] Syncing from official FERC registry...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/csv,*/*',
            'Referer': 'https://data.ferc.gov/company-registration/ferc-company-identifier-listing/'
        }
        
        req = urllib.request.Request(cls.OFFICIAL_URL, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                csv_data = response.read().decode('utf-8')
                
            df = pl.read_csv(io.StringIO(csv_data))
            name_col = "Organization Name" if "Organization Name" in df.columns else "Organization_Name"
            tech_id_col = "ID" if "ID" in df.columns else ("Company_Identifier" if "Company_Identifier" in df.columns else None)
            
            # Map available columns, use nulls for address fields if missing in official API for now
            official_df = df.select([
                pl.col("CID").alias("cid"),
                pl.col(name_col).alias("legal_name"),
                pl.col(tech_id_col).cast(pl.String).alias("technical_id") if tech_id_col else pl.lit("0").alias("technical_id"),
                pl.col("Program").alias("program") if "Program" in df.columns else pl.lit(None).cast(pl.String).alias("program"),
                pl.lit(None).cast(pl.String).alias("website"),
                pl.lit(None).cast(pl.String).alias("address"),
                pl.lit(None).cast(pl.String).alias("address2"),
                pl.lit(None).cast(pl.String).alias("city"),
                pl.lit(None).cast(pl.String).alias("state"),
                pl.lit(None).cast(pl.String).alias("zip"),
                pl.lit("1900-01-01").str.to_date("%Y-%m-%d").alias("effective_start_date"),
                pl.lit(None).cast(pl.Date).alias("effective_end_date")
            ])
            
            if os.path.exists(cls.REGISTRY_PATH):
                existing = pl.read_parquet(cls.REGISTRY_PATH)
                # Ensure existing has the full schema
                for col in official_df.columns:
                    if col not in existing.columns:
                        existing = existing.with_columns(pl.lit(None).cast(official_df.schema[col]).alias(col))
                
                merged = pl.concat([existing, official_df.select(existing.columns)]).unique(subset=["cid", "legal_name"], keep="last")
            else:
                merged = official_df
                
            os.makedirs(os.path.dirname(cls.REGISTRY_PATH), exist_ok=True)
            merged.write_parquet(cls.REGISTRY_PATH)
            cls._update_last_synced()
            log_progress(f"[STD-API] FERC Sync SUCCESS. Unified Mirror Size: {merged.height}", "SUCCESS")
            
        except Exception as e:
            log_progress(f"[STD-API] Online CID sync failed or timed out: {e}", "ERROR")
            log_progress("[STD-API] SUGGESTION: Please manually download the CID registry from FERC at: https://data.ferc.gov/company-registration/ferc-company-identifier-listing/ and save it as 'cid_master.csv' in 'tower_kernel/data/master/registry/'.", "WARN")
            # If we're blocked but have data, we just continue with last synced
            if not os.path.exists(cls.REGISTRY_PATH):
                cls.bootstrap_sample_data()

    @classmethod
    def ensure_synced(cls):
        """Checks if a sync is needed today and executes if required."""
        last_synced = cls._get_last_synced_date()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if last_synced != today:
            cls.sync_official_registry()

    @classmethod
    def _get_last_synced_date(cls) -> str:
        if not os.path.exists(cls.METADATA_PATH):
            return ""
        try:
            with open(cls.METADATA_PATH, 'r') as f:
                return json.load(f).get("last_synced_date", "")
        except:
            return ""

    @classmethod
    def _update_last_synced(cls):
        today = datetime.now().strftime("%Y-%m-%d")
        os.makedirs(os.path.dirname(cls.METADATA_PATH), exist_ok=True)
        with open(cls.METADATA_PATH, 'w') as f:
            json.dump({"last_synced_date": today}, f)
