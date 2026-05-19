import polars as pl
import json
import yaml
import os
from pathlib import Path
import sys

# Add the tower_kernel source to path
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel" / "src"))

from tower_kernel.rules.eqr import run_benchmarked_validation, _normalize_schema

CID = "C000041"
LAKE_BASE = WORKSPACE_ROOT / "tower_kernel" / "data" / "lake" / CID / "2025-Q1" / "silver"
TX_PATH = LAKE_BASE / "transactions.parquet"
IDENT_PATH = LAKE_BASE / "ident.parquet"
CONTRACT_PATH = LAKE_BASE / "contracts.parquet"
OUTPUT_FILE = WORKSPACE_ROOT / "scratch" / "validation_results.json"

def main():
    print(f"Loading data for {CID}...")
    ldf = _normalize_schema(pl.scan_parquet(TX_PATH))
    ident_ldf = _normalize_schema(pl.scan_parquet(IDENT_PATH)) if IDENT_PATH.exists() else None
    contract_ldf = _normalize_schema(pl.scan_parquet(CONTRACT_PATH)) if CONTRACT_PATH.exists() else None

    metadata = {
        "company_id": CID,
        "period": "2025-Q1"
    }

    print("Running bench-marked validation engine on ALL rules...")
    combined_errors, stats = run_benchmarked_validation(
        ldf=ldf,
        identity_ldf=ident_ldf,
        contract_ldf=contract_ldf,
        metadata=metadata
    )
    
    # Load registry to maintain order and get names
    registry_path = WORKSPACE_ROOT / "tower_kernel" / "src" / "tower_kernel" / "rules" / "eqr_rules_registry.yaml"
    with open(registry_path, "r") as f:
        registry = yaml.safe_load(f)

    # Map stats for quick lookup
    stats_map = {s["rule_id"]: s for s in stats}
    
    cid_results = []
    
    for rule_id, rule_info in registry.items():
        if rule_id not in stats_map:
            continue
            
        stat = stats_map[rule_id]
        
        # Calculate result string
        error_count = stat.get('error_count', 0)
        failure = stat.get('engine_failure')
        
        if failure:
            result = f"Failed Execution: {failure}"
        elif error_count > 0:
            result = f"Failed ({error_count} violations)"
        else:
            result = "Passed"
            
        cid_results.append({
            "code": rule_id,
            "name": rule_info.get("name", rule_info.get("description", "Rule")),
            "result": result
        })

    # Load existing results if file exists to extend it
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r") as f:
                all_results = json.load(f)
        except Exception:
            all_results = {}
    else:
        all_results = {}

    # Key by CID
    all_results[CID] = cid_results

    # Save
    os.makedirs(OUTPUT_FILE.parent, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"Results exported to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
