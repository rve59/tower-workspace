import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
import polars as pl

# Add TOWER paths
WORKSPACE_ROOT = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE"
sys.path.append(os.path.join(WORKSPACE_ROOT, "tower_kernel/src"))

from tower_kernel.rules.transpiler import CypherTranspiler, RelationalContext
from tower_kernel.services.audit_agent import RegulatoryAuditorAgent, ForensicBrief

REGISTRY_PATH = os.path.join(WORKSPACE_ROOT, "tower_kernel/src/tower_kernel/rules/eqr_rules_registry.json")

def run_zero_copy_audit(cid, period):
    print(f"--- TOWER ZERO-COPY AUDIT ENGINE ---")
    print(f"Target CID: {cid}")
    print(f"Target Period: {period}")
    print(f"Strategy: Polars Transpilation (Pillar-to-Pillar)")

    # 1. Setup Pillars (Lazy Scanning)
    lake_path = Path(WORKSPACE_ROOT) / f"tower_kernel/data/lake/{cid}/{period}/bronze"
    
    pillars = {
        "Transactions": pl.scan_parquet(lake_path / "transactions.parquet"),
        "Contracts": pl.scan_parquet(lake_path / "contracts.parquet"),
        "Ident": pl.scan_parquet(lake_path / "ident.parquet"),
        "Index": pl.scan_parquet(lake_path / "index.parquet")
    }
    
    # Pre-calculate table counts for telemetry
    table_counts = {
        "Transactions": pillars["Transactions"].select(pl.len()).collect().item(),
        "Contracts": pillars["Contracts"].select(pl.len()).collect().item(),
        "Ident": pillars["Ident"].select(pl.len()).collect().item()
    }
    print(f"Table Scale: {table_counts}")

    context = RelationalContext(pillars=pillars)
    
    # 2. Load Registry
    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)

    # 3. Execution Loop
    print("\nExecuting Logic Gates (Transpiled)...")
    audit_results = []
    
    for rule_id, rule_meta in registry.items():
        print(f"  [GATE] {rule_id}: {rule_meta['description']}...", end="", flush=True)
        
        # Transpile Cypher to Polars
        cypher_query = rule_meta['cypher'].replace("{{CID}}", cid).replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
        
        start_time = datetime.now()
        try:
            # Generate the violation LazyFrame
            violations_ldf = CypherTranspiler.transpile(cypher_query, context)
            
            # Execute (Collect)
            violations_df = violations_df = violations_ldf.collect()
            v_count = violations_df.height
            
            duration = (datetime.now() - start_time).total_seconds()
            print(f" DONE ({v_count:,} violations, {duration:.2f}s)")
            
            # Telemetry Payload
            telemetry = {
                "rows_scanned": table_counts["Transactions"],
                "execution_time_sec": round(duration, 4),
                "throughput_rows_per_sec": int(table_counts["Transactions"] / duration) if duration > 0 else 0,
                "engine": "Polars-Zero-Copy-Transpiler"
            }

            if v_count > 0:
                # Generate Forensic Brief
                samples = violations_df.head(5).to_dicts()
                brief_obj = ForensicBrief(
                    rule_id=rule_id,
                    category=rule_meta.get("severity", "Significant"),
                    description=rule_meta["description"],
                    error_count=v_count,
                    total_count=table_counts["Transactions"],
                    sample_records=samples,
                    telemetry=telemetry
                )
                
                offline_brief = RegulatoryAuditorAgent._render_offline_brief(brief_obj)
                
                audit_results.append({
                    "rule_id": rule_id,
                    "severity": rule_meta.get("severity"),
                    "count": v_count,
                    "description": rule_meta["description"],
                    "brief": offline_brief,
                    "telemetry": telemetry
                })
        except Exception as e:
            print(f" FAILED: {e}")

    # 4. Final Reporting
    total_detected = sum(r["count"] for r in audit_results)
    print("\n" + "="*70)
    print(f"ZERO-COPY AUDIT SUMMARY: {total_detected:,} Total Issues Detected.")
    print("="*70)

    # Generate Markdown Report
    REPORT_DIR = Path(WORKSPACE_ROOT) / "tower_kernel/data/reports"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORT_DIR / f"audit_report_ZERO_COPY_{cid}_{period}.md"
    
    with open(report_file, 'w') as md:
        md.write(f"# Zero-Copy Forensic Audit Report: {cid} ({period})\n\n")
        md.write(f"**Status**: Audit Complete (Polars Shadow Mode)\n")
        md.write(f"**Engine**: TOWER Transpiler v2.0 (Zero-Copy)\n\n")
        md.write(f"## 1. Executive Summary\nDetected {total_detected:,} violations across {len(audit_results)} logic gates.\n\n")
        md.write(f"## 2. Findings Matrix\n")
        md.write(f"| Rule ID | Severity | Count | Description |\n")
        md.write(f"| :--- | :--- | :--- | :--- |\n")
        for r in audit_results:
            md.write(f"| {r['rule_id']} | {r['severity']} | {r['count']:,} | {r['description']} |\n")
        
        md.write(f"\n## 3. Forensic Briefings\n")
        for r in audit_results:
            md.write(f"### Rule {r['rule_id']}\n\n{r['brief']}\n\n---\n")

    print(f"\n[SUCCESS] Zero-Copy Report generated at: {report_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOWER Zero-Copy Audit Engine")
    parser.add_argument("--cid", required=True, help="Company Identifier")
    parser.add_argument("--period", required=True, help="Filing Period")
    
    args = parser.parse_args()
    run_zero_copy_audit(args.cid, args.period)
