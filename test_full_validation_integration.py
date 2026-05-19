import polars as pl
import os
import sys
import time
import subprocess
import traceback
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pyarrow.parquet as pq

# Add the tower_kernel source to path
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel" / "src"))

from tower_kernel.rules.eqr import run_benchmarked_validation, _normalize_schema
from tower_kernel.services.diagnostic import DiagnosticService

CID = "C000171"
LAKE_BASE = WORKSPACE_ROOT / "tower_kernel" / "data" / "lake" / CID / "2025-Q1" / "silver"
TX_PATH = LAKE_BASE / "transactions.parquet"
IDENT_PATH = LAKE_BASE / "ident.parquet"
CONTRACT_PATH = LAKE_BASE / "contracts.parquet"

LOG_DIR = WORKSPACE_ROOT / "tower_kernel" / "asdlc" / "projmgt" / "03_testing" / "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = LOG_DIR / "test_full_validation_integration.log"

# Clear log at start of run
with open(LOG_FILE, "w") as f:
    pass

def log(message: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    with open(LOG_FILE, "a") as f:
        f.write(formatted + "\n")

def run_services():
    log("Restarting UI/UX and services with ./run_tower.sh")
    try:
        subprocess.run(["./run_tower.sh"], check=True, cwd=WORKSPACE_ROOT)
    except Exception as e:
        log(f"CRITICAL: Failed to restart services: {e}")

CATEGORY_MAP = {
    "SCHEMA":     "Type 1",
    "STRUCTURAL": "Type 1",
    "MANDATORY":  "Type 2", 
    "LOOKUP":     "Type 2",
    "IDENTITY":   "Type 2",
    "REGISTRY":   "Type 2",
    "ARITHMETIC": "Type 3", 
    "CONSISTENCY": "Type 3", 
    "CONDITIONAL": "Type 3",
    "DEDUP":       "Type 3",
    "HISTORICAL": "Type 4",
    "BOUNDS":     "Type 5",
    "AUDIT":      "Type 5"
}

def get_all_rules() -> List[Dict[str, Any]]:
    registry_path = WORKSPACE_ROOT / "tower_kernel" / "src" / "tower_kernel" / "rules" / "eqr_rules_registry.yaml"
    import yaml
    with open(registry_path, "r") as f:
        json_registry = yaml.safe_load(f)
        
    all_rules = []
    for rule_id, rule_info in json_registry.items():
        severity = rule_info.get("severity", "Error")
        if severity == "Critical":
            category = "CONSISTENCY"
        elif severity == "Warning":
            category = "BOUNDS"
        else:
            if rule_id.startswith("F.16.4") or rule_id.startswith("F.24.1") or rule_id.startswith("F.TYPE"):
                category = "STRUCTURAL"
            else:
                category = "MANDATORY"
                
        all_rules.append({
            "id": rule_id,
            "category": category,
            "desc": rule_info.get("description", ""),
            "cypher": rule_info.get("cypher", ""),
            "source": "cypher"
        })
    return all_rules

def run_rule(rule: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, int]:
    """
    Returns (success, error_count)
    Success is False if Kernel Error occurs.
    """
    ldf = context["ldf"]
    ident_ldf = context["ident_ldf"]
    contract_ldf = context["contract_ldf"]
    metadata = context["metadata"]
    
    try:
        from tower_kernel.rules.transpiler import CypherTranspiler, RelationalContext
        
        rel_context = RelationalContext({
            "Transactions": ldf,
            "Ident": ident_ldf if ident_ldf is not None else pl.LazyFrame(schema={"tower_unique_id": pl.String}),
            "Contracts": contract_ldf if contract_ldf is not None else pl.LazyFrame(schema={"tower_unique_id": pl.String})
        })
        
        cypher = rule["cypher"]
        cid_val = metadata.get("company_id", metadata.get("cid", "UNKNOWN"))
        import datetime
        date_val = datetime.date.today().strftime("%Y-%m-%d")
        cypher = cypher.replace("{{CID}}", cid_val).replace("{{DATE}}", date_val)
        
        # Execute transpilation
        violation_ldf = CypherTranspiler.transpile(cypher, rel_context)
        res = violation_ldf.collect()
        
        log(f"      [OK] Rule executed successfully. {'No violations found.' if res.height == 0 else f'Found {res.height} proper errors.'}")
        
        # Forensic brief trigger
        _total_count = ldf.select(pl.len()).collect().item()
        _violation_rate = res.height / _total_count if _total_count > 0 else 0.0
        
        if _violation_rate >= 0.025 or res.height > 5000:
            log(f"      [AGENT] Trigger threshold met ({_violation_rate:.1%} / {res.height:,} errors). Building forensic brief for {rule['id']}...")
            try:
                from tower_kernel.services.audit_agent import RegulatoryAuditorAgent
                dummy_total_df = pl.DataFrame([pl.Series("dummy", [None] * _total_count)])
                
                rule_spec = {
                    "rule_id": rule["id"],
                    "category": rule["category"],
                    "description": rule["desc"]
                }
                
                dest = RegulatoryAuditorAgent.resolve_audit_path(
                    rule_id=rule["id"],
                    cid=context["cid"],
                    year=context["year"],
                    quarter=context["quarter"],
                    tier=context["tier"]
                )
                
                RegulatoryAuditorAgent.build_forensic_brief(
                    rule_spec=rule_spec,
                    error_df=res,
                    total_df=dummy_total_df,
                    cid=context["cid"],
                    year=context["year"],
                    quarter=context["quarter"],
                    tier=context["tier"]
                )
                log(f"      [AGENT] Forensic brief saved → {dest.relative_to(WORKSPACE_ROOT)}")
            except Exception as agent_err:
                log(f"      [AGENT] Warning: ForensicSummarizer failed ({agent_err}).")
                
        return True, res.height
    except Exception as e:
        log(f"!!! KERNEL ERROR in {rule['id']}: {e}")
        return False, 0

def main():
    if not TX_PATH.exists():
        print(f"Error: Data for {CID} not found at {TX_PATH}")
        return

    # Load context
    log(f"Initializing Context for {CID}...")
    ldf = _normalize_schema(pl.scan_parquet(TX_PATH))
    ident_ldf = _normalize_schema(pl.scan_parquet(IDENT_PATH)) if IDENT_PATH.exists() else None
    contract_ldf = _normalize_schema(pl.scan_parquet(CONTRACT_PATH)) if CONTRACT_PATH.exists() else None
    
    # Historical discovery
    previous_ldf = DiagnosticService._discover_previous_quarter(str(TX_PATH))
    
    # Registry sync
    from tower_kernel.services.registry_mirror import RegistryMirrorService
    RegistryMirrorService.ensure_synced()
    registry_ldf = RegistryMirrorService.get_mirror_ldf()
    
    # Metadata
    meta = pq.read_metadata(TX_PATH).metadata
    metadata = {k.decode("utf-8"): v.decode("utf-8") if isinstance(v, bytes) else v for k, v in meta.items()} if meta else {}

    # Derive audit placement context from the lake path
    lake_parts = LAKE_BASE.parts
    tier_name  = lake_parts[-1]           # e.g. "bronze"
    period_str = lake_parts[-2]           # e.g. "2025-Q1"
    cid_str    = lake_parts[-3]           # e.g. "C000171"
    year_str, quarter_str = period_str.split("-")  # "2025", "Q1"

    context = {
        "ldf": ldf,
        "ident_ldf": ident_ldf,
        "contract_ldf": contract_ldf,
        "previous_ldf": previous_ldf,
        "registry_ldf": registry_ldf,
        "metadata": metadata,
        # Audit placement
        "cid": cid_str,
        "year": year_str,
        "quarter": quarter_str,
        "tier": tier_name,
    }

    all_rules = get_all_rules()
    
    # Group rules by Type
    types = ["Type 1", "Type 2", "Type 3", "Type 4", "Type 5"]
    rules_by_type = {t: [] for t in types}
    for r in all_rules:
        t = CATEGORY_MAP.get(r["category"], "Type 5")
        rules_by_type[t].append(r)

    log("Starting Full Integration Test Suite...")
    
    current_type_idx = 0
    while current_type_idx < len(types):
        t_name = types[current_type_idx]
        rules = rules_by_type[t_name]
        
        log(f"--- Running {t_name} validations ---")
        
        all_rules_passed_in_type = True
        for i, rule in enumerate(rules):
            log(f"TEST {i+1}/{len(rules)}: {rule['id']} ({rule['category']})")
            success, err_count = run_rule(rule, context)
            
            if not success:
                log(f"FAILED: Kernel Error in {rule['id']}. Restarting from Type 1 - Test 1.")
                run_services()
                current_type_idx = 0 # Restart from Type 1
                all_rules_passed_in_type = False
                break
            else:
                pass
        
        if all_rules_passed_in_type:
            log(f"Completed all {t_name} validations.")
            current_type_idx += 1
        else:
            time.sleep(2)
            
    log("FULL INTEGRATION TEST COMPLETE. All validations passed without kernel errors.")

if __name__ == "__main__":
    main()
