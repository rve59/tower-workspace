import polars as pl
import os
import sys
import time
import subprocess
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pyarrow.parquet as pq
import inspect

# Add the tower_kernel source to path
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel" / "src"))

from tower_kernel.rules.eqr import (
    run_benchmarked_validation, 
    registry, 
    lake_registry, 
    registry_rule_registry, 
    METADATA_RULES, 
    get_metadata_predicate,
    _normalize_schema
)
from tower_kernel.services.diagnostic import DiagnosticService

CID = "C000171"
LAKE_BASE = WORKSPACE_ROOT / "tower_kernel" / "data" / "lake" / CID / "2025-Q1" / "bronze"
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

def get_all_rules():
    all_rules = []
    
    # 1. Metadata rules (Phase 0)
    for meta_rule in METADATA_RULES:
        rule_spec = {
            "id": meta_rule["id"],
            "category": meta_rule["category"],
            "desc": meta_rule["desc"],
            "meta_rule": meta_rule,
            "source": "metadata"
        }
        all_rules.append(rule_spec)
        
    # 2. Registry rules
    for rule in registry.rules:
        all_rules.append({
            "id": rule["rule_id"],
            "category": rule["category"],
            "desc": rule["description"],
            "func": rule["func"],
            "source": "functional"
        })
        
    # 3. Lake rules
    for rule in lake_registry.rules:
        all_rules.append({
            "id": rule["rule_id"],
            "category": rule["category"],
            "desc": rule["description"],
            "func": rule["func"],
            "source": "lake"
        })
        
    # 4. Registry-aware rules
    for rule in registry_rule_registry.rules:
        all_rules.append({
            "id": rule["rule_id"],
            "category": rule["category"],
            "desc": rule["description"],
            "func": rule["func"],
            "source": "registry"
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
    previous_ldf = context["previous_ldf"]
    registry_ldf = context["registry_ldf"]
    metadata = context["metadata"]
    
    try:
        source = rule["source"]
        rule_id = rule["id"]
        
        # Determine target LDF
        target_ldf = ldf
        if rule_id.startswith("F.16") or "IDENT" in rule_id:
            target_ldf = ident_ldf
        elif rule_id.startswith("F.20") or rule_id.startswith("F.21") or "CONTRACT" in rule_id:
            target_ldf = contract_ldf
            
        if target_ldf is None:
            # Skip if target table missing
            return True, 0

        # Check column existence for metadata rules (SCHEMA rules)
        if source == "metadata":
            col = rule["meta_rule"]["col"]
            available_cols = target_ldf.collect_schema().names()
            if col not in available_cols:
                return True, 0

        # Execute based on source type
        if source == "metadata":
            func = get_metadata_predicate(rule["meta_rule"], metadata=metadata)
            res = func(target_ldf).collect()
        elif source == "functional":
            func = rule["func"]
            sig = inspect.signature(func)
            kwargs = {"metadata": metadata, "contract_ldf": contract_ldf, "identity_ldf": ident_ldf}
            call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            if "ldf" in sig.parameters: call_kwargs["ldf"] = target_ldf
            elif "identity_ldf" in sig.parameters: call_kwargs["identity_ldf"] = target_ldf
            res = func(**call_kwargs).collect()
        elif source == "lake":
            func = rule["func"]
            res = func(target_ldf, previous_ldf).collect()
        elif source == "registry":
            func = rule["func"]
            res = func(target_ldf, registry_ldf, metadata).collect()
        else:
            return True, 0
            
        # Rule finished
        log(f"      [OK] Rule executed successfully. {'No violations found.' if res.height == 0 else f'Found {res.height} proper errors.'}")
        
        # FORENSIC BRIEF TRIGGER — offline compression only, NO Gemini call.
        # Dual Threshold: Fires if violation rate >= 2.5% OR absolute count > 5,000.
        # This captures both high-density systemic issues and high-volume mass failures.
        _total_count = target_ldf.select(pl.len()).collect().item()
        _violation_rate = res.height / _total_count if _total_count > 0 else 0.0

        if _violation_rate >= 0.025 or res.height > 5000:
            log(f"      [AGENT] Trigger threshold met ({_violation_rate:.1%} / {res.height:,} errors). Building forensic brief for {rule_id}...")
            try:
                from tower_kernel.services.audit_agent import RegulatoryAuditorAgent

                rule_spec = {
                    "rule_id": rule_id,
                    "category": rule.get("category", "UNKNOWN"),
                    "description": rule.get("desc", ""),
                    "col": rule.get("meta_rule", {}).get("col") if source == "metadata" else None,
                }

                total_df = target_ldf.collect()

                # Save under data/audit/<CID>/<YYYY-QQ>/<tier>/
                brief = RegulatoryAuditorAgent.build_forensic_brief(
                    rule_spec=rule_spec,
                    error_df=res,
                    total_df=total_df,
                    cid=context["cid"],
                    year=context["year"],
                    quarter=context["quarter"],
                    tier=context["tier"],
                )
                dest = RegulatoryAuditorAgent.resolve_audit_path(
                    rule_id=rule_id,
                    cid=context["cid"],
                    year=context["year"],
                    quarter=context["quarter"],
                    tier=context["tier"],
                )
                log(f"      [AGENT] Forensic brief saved → {dest.relative_to(WORKSPACE_ROOT)}")
                log(f"      [AGENT] Submit to Gemini via TOWER UI or submit_to_gemini() when ready.")
            except Exception as agent_err:
                log(f"      [AGENT] Warning: ForensicSummarizer failed ({agent_err}).")
            
        return True, res.height
    except Exception as e:
        log(f"!!! KERNEL ERROR in {rule['id']}: {e}")
        # log(traceback.format_exc())
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
    # Pattern: lake/<CID>/<YYYY-QQ>/<tier>/transactions.parquet
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
                # log(f"      [OK] Rule executed successfully. {'No violations found.' if err_count == 0 else f'Found {err_count} proper errors.'}")
                pass
        
        if all_rules_passed_in_type:
            log(f"Completed all {t_name} validations.")
            current_type_idx += 1
        else:
            # If we hit a kernel error, the loop resets via current_type_idx = 0
            # We also sleep a bit to avoid infinite tight loop if restart fails
            time.sleep(2)
            
    log("FULL INTEGRATION TEST COMPLETE. All validations passed without kernel errors.")

if __name__ == "__main__":
    main()
