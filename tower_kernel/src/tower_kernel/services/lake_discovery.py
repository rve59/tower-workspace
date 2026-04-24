from pathlib import Path
from typing import List, Dict, Any
from tower_kernel import config
import polars as pl
import json

class LakeDiscoveryService:
    """
    Scans the TOWER Data Lake to discover existing filings across all tiers.
    Organizes them into a hierarchy for the UI.
    """

    @staticmethod
    def get_hierarchical_filings() -> List[Dict[str, Any]]:
        """
        Returns a list of filings grouped by Tier -> Company -> Period.
        """
        # 1. Load CID Master for legal name resolution
        cid_map = {}
        if config.PATH_CID_MASTER.exists():
            try:
                df = pl.read_parquet(config.PATH_CID_MASTER)
                # Map cid to legal_name
                cid_map = dict(df.select(["cid", "legal_name"]).unique().iter_rows())
            except Exception as e:
                print(f"Warning: Failed to load CID Master: {e}")

        # 2. Scan Lake Root
        results = {
            config.TIER_BRONZE: {},
            config.TIER_SILVER: {},
            config.TIER_GOLD: {}
        }

        if not config.LAKE_ROOT.exists():
            return []

        # Find all .parquet files to discover active filings
        for parquet_path in config.LAKE_ROOT.rglob("*.parquet"):
            parts = parquet_path.relative_to(config.LAKE_ROOT).parts
            
            # Identify CID (always first part)
            cid = parts[0]
            
            # Strictly filter for real FERC CIDs (C + digits)
            # This removes sample data like TEST_FILER, test_cid_999, etc.
            if not (cid.startswith("C") and cid[1:].isdigit()):
                continue
            
            # Heuristic for Tier and Period
            tier = None
            year = None
            quarter = None
            
            for part in parts:
                if part in [config.TIER_BRONZE, config.TIER_SILVER, config.TIER_GOLD]:
                    tier = part
                if "-" in part and len(part) >= 7: # e.g. 2024-Q1
                    subparts = part.split("-")
                    if subparts[0].isdigit() and subparts[1].startswith("Q"):
                        year, quarter = subparts
                elif part.isdigit() and len(part) == 4:
                    year = part
                elif part.startswith("Q") and len(part) == 2 and part[1].isdigit():
                    quarter = part

            if not tier:
                continue
            
            # Default period if not found
            if not year: year = "Unknown"
            if not quarter: quarter = ""
            
            if cid not in results[tier]:
                results[tier][cid] = {
                    "cid": cid,
                    "name": cid_map.get(cid, cid),
                    "periods": {}
                }
            
            period_key = f"{year}-{quarter}"
            if period_key not in results[tier][cid]["periods"]:
                results[tier][cid]["periods"][period_key] = {
                    "id": f"{cid}-{year}-{quarter}-{tier}",
                    "year": year,
                    "quarter": quarter,
                    "period": period_key.strip("-"),
                    "status": LakeDiscoveryService._infer_status(tier),
                    "tier": tier
                }

        # 3. Format for UI and sort
        formatted = []
        tier_labels = {
            config.TIER_BRONZE: "Bronze Lake",
            config.TIER_SILVER: "Silver Vault",
            config.TIER_GOLD: "Gold Archive"
        }

        for tier in [config.TIER_BRONZE, config.TIER_SILVER, config.TIER_GOLD]:
            companies_dict = results[tier]
            companies = []
            for cid, comp_data in companies_dict.items():
                periods = list(comp_data["periods"].values())
                # Sort periods descending
                periods.sort(key=lambda x: (x["year"], x["quarter"]), reverse=True)
                companies.append({
                    "cid": cid,
                    "name": comp_data["name"],
                    "periods": periods
                })
            
            # Sort companies by name
            companies.sort(key=lambda x: x["name"])

            formatted.append({
                "id": tier,
                "label": tier_labels[tier],
                "companies": companies
            })

        return formatted

    @staticmethod
    def _infer_status(tier: str) -> str:
        if tier == config.TIER_BRONZE: return "DRAFT"
        if tier == config.TIER_SILVER: return "VALIDATED"
        if tier == config.TIER_GOLD: return "ARCHIVED"
        return "UNKNOWN"

    @staticmethod
    def resolve_filing_path(filing_id: str) -> Path | None:
        """
        Resolves a filing ID (cid-year-quarter-tier) to the primary transactions parquet file.
        """
        parts = filing_id.split("-")
        if len(parts) < 4:
            return None
        
        cid, year, quarter, tier = parts[0], parts[1], parts[2], parts[3]
        
        # Check standard path
        path = config.get_tier_path(cid, tier, year, quarter) / config.TABLE_TRANSACTIONS
        if path.exists():
            return path
            
        # Fallback recursive search if not in standard path
        for p in config.LAKE_ROOT.rglob("*.parquet"):
            if cid in p.parts and tier in p.parts:
                # Basic check for year/quarter in path
                p_str = str(p)
                if year in p_str and quarter in p_str:
                    return p
                    
        return None
