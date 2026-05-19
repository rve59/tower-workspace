import polars as pl
import yaml
import json
import os
from pathlib import Path
import sys

# Setup imports
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel" / "src"))
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel"))

from tower_kernel.rules.eqr import run_benchmarked_validation
from tests.test_positive_assertions import get_golden_data, load_mutations

OUTPUT_JSON = WORKSPACE_ROOT / "scratch" / "validation_results.json"
REGISTRY_PATH = WORKSPACE_ROOT / "tower_kernel" / "src" / "tower_kernel" / "rules" / "eqr_rules_registry.yaml"

def generate_harness_results():
    print("Generating Test Harness Results...")

    # Load registry for rule codes
    with open(REGISTRY_PATH, "r") as f:
        registry = yaml.safe_load(f)
    rule_codes = list(registry.keys())

    # Load existing results to append to
    if OUTPUT_JSON.exists():
        try:
            with open(OUTPUT_JSON, "r") as f:
                all_results = json.load(f)
        except Exception:
            all_results = {}
    else:
        all_results = {}

    # 1. Golden Filing
    ident, contract, tx = get_golden_data()
    metadata = {"company_id": "TEST_GOLDEN", "period": "2025-Q1"}
    
    print("Evaluating Golden Filing...")
    _, stats = run_benchmarked_validation(ldf=tx, identity_ldf=ident, contract_ldf=contract, metadata=metadata)
    stats_map = {s["rule_id"]: s.get("error_count", 0) for s in stats}
    
    golden_results = []
    for code in rule_codes:
        golden_results.append({
            "code": code,
            "name": registry[code].get("name", ""),
            "result": "Failed" if stats_map.get(code, 0) > 0 else "Passed"
        })
    all_results["TEST_GOLDEN"] = golden_results

    # 2. Mutated Filings
    mutations = load_mutations()
    for rule_id, config in mutations:
        ident, contract, tx = get_golden_data()
        target = config.get("target", "Transactions")
        updates = config.get("updates", {})
        
        exprs = []
        for col, val in updates.items():
            if val is None:
                exprs.append(pl.lit(None).cast(pl.String).alias(col))
            else:
                exprs.append(pl.lit(str(val)).alias(col))
                
        if target == "Transactions":
            tx = tx.with_columns(exprs)
        elif target == "Contracts":
            contract = contract.with_columns(exprs)
        elif target == "Ident":
            ident = ident.with_columns(exprs)

        cid = f"TEST_{rule_id}"
        metadata = {"company_id": cid, "period": "2025-Q1"}
        
        print(f"Evaluating Mutated Filing: {cid}...")
        _, stats = run_benchmarked_validation(ldf=tx, identity_ldf=ident, contract_ldf=contract, metadata=metadata)
        stats_map = {s["rule_id"]: s.get("error_count", 0) for s in stats}
        
        mutated_results = []
        for code in rule_codes:
            err_count = stats_map.get(code, 0)
            res_str = f"Failed ({err_count} violations)" if err_count > 0 else "Passed"
            mutated_results.append({
                "code": code,
                "name": registry[code].get("name", ""),
                "result": res_str
            })
        all_results[cid] = mutated_results

    # Save to JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_results, f, indent=2)
    print("Test harness results injected into validation_results.json!")

if __name__ == "__main__":
    generate_harness_results()
