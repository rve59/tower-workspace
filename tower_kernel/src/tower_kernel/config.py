import os
from pathlib import Path

# Authoritative Root of the TOWER Kernel Package
PACKAGE_ROOT = Path(__file__).parent.parent.parent.resolve()

# Authoritative Data Lake Configuration
LAKE_ROOT = PACKAGE_ROOT / "data" / "lake"
MASTER_ROOT = PACKAGE_ROOT / "data" / "master"
REGISTRY_ROOT = MASTER_ROOT / "registry"

# Authoritative Metadata Paths
PATH_DISCOVERY_INDEX = REGISTRY_ROOT / "discovery_index.parquet"
PATH_CID_MASTER = REGISTRY_ROOT / "cid_master.parquet"
PATH_CID_METADATA = REGISTRY_ROOT / "cid_metadata.json"

# Ingestion Table Identifiers
TABLE_TRANSACTIONS = "transactions.parquet"
TABLE_IDENT = "ident.parquet"
TABLE_CONTRACTS = "contracts.parquet"
TABLE_INDEX = "index.parquet"

# Valid Data Tiers
TIER_BRONZE = "bronze"
TIER_SILVER = "silver"
TIER_GOLD = "gold"

# CID-Scoped Operational Areas
TIER_INBOX = "inbox"
TIER_REPORTS = "reports"

def get_tier_path(cid: str, tier: str = TIER_BRONZE, year: str = None, quarter: str = None) -> Path:
    """
    Returns the authoritative Path for a specific company's data lake tier.
    Organized by: CID / YYYY-QQ / tier
    Ensures the directory exists.
    """
    if year and quarter:
        # Standardize on 'Q1', 'Q2' etc
        q_str = str(quarter)
        if not q_str.startswith("Q"):
            q_str = f"Q{q_str}"
        path = LAKE_ROOT / str(cid) / f"{year}-{q_str}" / tier
    else:
        # Fallback for general cid level
        path = LAKE_ROOT / str(cid) / tier
        
    path.mkdir(parents=True, exist_ok=True)
    return path

# Shared API Registry
HUB_LOG_URL = os.getenv("HUB_LOG_URL", "http://localhost:9042/v1/system/logs/append")
