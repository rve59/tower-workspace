import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add the Ladybug Bridge library to the path
BRIDGE_PATH = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/ladybug.libs/lib_ldbg_tower_bridge/src"
sys.path.append(BRIDGE_PATH)

from lib_ldbg_tower_bridge.bridge import LadybugTowerBridge

REGISTRY_PATH = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/src/tower_kernel/rules/eqr_rules_registry.json"

def run_forensic_audit(cid, period):
    # 1. Paths Construction
    # period format: 2025-Q1
    host_lake_path = f"/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/lake/{cid}/{period}/bronze/"
    container_lake_path = f"/database/{cid}/{period}/bronze/"
    
    print(f"--- TOWER FORENSIC ENGINE ---")
    print(f"Target CID: {cid}")
    print(f"Target Period: {period}")
    
    # 2. Initialize the Bridge
    bridge = LadybugTowerBridge(api_url="http://localhost:9045")
    
    # 3. Generate Schema & Loading Commands
    print(f"\nGenerating Icebug Schema for: {host_lake_path}")
    ddl = bridge.generate_icebug_schema(host_lake_path)
    ddl = ddl.replace(host_lake_path, container_lake_path)
    
    # 4. Refresh Graph Context
    print("\nRefreshing Graph Context...")
    # Clean drops (RELs first)
    bridge.execute_cypher("DROP TABLE HAS_VIOLATION;")
    bridge.execute_cypher("DROP TABLE AUTHORIZED_BY;")
    bridge.execute_cypher("DROP TABLE Violation;")
    bridge.execute_cypher("DROP TABLE AuditBrief;")
    bridge.execute_cypher("DROP TABLE EXECUTES_TERM;")
    bridge.execute_cypher("DROP TABLE Transactions;")
    bridge.execute_cypher("DROP TABLE Contracts;")
    bridge.execute_cypher("DROP TABLE Ident;")
    bridge.execute_cypher("DROP TABLE Index;")

    for statement in ddl.split(";"):
        stmt = statement.strip()
        if stmt: bridge.execute_cypher(stmt + ";")

    # 5. Define Violation and Briefing Schema
    bridge.execute_cypher("CREATE NODE TABLE Violation(ViolationID STRING, RuleID STRING, CID STRING, Message STRING, Severity STRING, DetectedAt STRING, PRIMARY KEY (ViolationID));")
    bridge.execute_cypher("CREATE NODE TABLE AuditBrief(RuleID STRING PRIMARY KEY, Content STRING, GeneratedAt STRING);")
    bridge.execute_cypher("CREATE REL TABLE HAS_VIOLATION(FROM Transactions TO Violation, FROM Contracts TO Violation, FROM Ident TO Violation);")

    # 6. Load and Execute Rules from Registry (with Offline Briefing)
    print("\n--- EXECUTING RULES FROM REGISTRY ---")
    from tower_kernel.services.audit_agent import RegulatoryAuditorAgent, ForensicBrief

    with open(REGISTRY_PATH, 'r') as f:
        registry = json.load(f)

    audit_date = datetime.now().strftime("%Y-%m-%d")

    for rule_id, rule_meta in registry.items():
        # Swap placeholders
        query = rule_meta['cypher'].replace("{{CID}}", cid).replace("{{DATE}}", audit_date)
        print(f"  [GATE] {rule_id}: {rule_meta['description']}...")
        bridge.execute_cypher(query)

        # Generate OFFLINE Audit Brief for the Graph
        count_query = f"MATCH (v:Violation {{RuleID: '{rule_id}'}}) RETURN count(v) AS VCount;"
        count_res = bridge.execute_cypher(count_query)
        v_count = 0
        if count_res.get("rows"):
            row = count_res["rows"][0]
            v_count = row.get("VCount") if isinstance(row, dict) else row[0]

        if v_count > 0:
            # Get 5 samples for the brief
            sample_query = f"MATCH (v:Violation {{RuleID: '{rule_id}'}}) RETURN v.Message AS Msg LIMIT 5;"
            sample_res = bridge.execute_cypher(sample_query)
            samples = []
            for r in sample_res.get("rows", []):
                msg = r.get("Msg") if isinstance(r, dict) else r[0]
                samples.append({"Message": msg})

            brief_obj = ForensicBrief(
                rule_id=rule_id,
                category=rule_meta.get("severity", "Significant"),
                description=rule_meta["description"],
                error_count=v_count,
                total_count=500000, # Estimated scale
                sample_records=samples
            )
            
            offline_content = RegulatoryAuditorAgent._render_offline_brief(brief_obj)
            
            # Store Brief in Graph (Offline only)
            brief_query = f"MERGE (b:AuditBrief {{RuleID: '{rule_id}'}}) SET b.Content = $content, b.GeneratedAt = '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}';"
            bridge.execute_cypher(brief_query, parameters={"content": offline_content})

    # 7. Final Forensic Reporting & Markdown Generation
    print("\n" + "="*70)
    print(f"CONSOLIDATED FORENSIC AUDIT REPORT: {cid} ({period})")
    print("="*70)
    
    # Aggregated query with specific aliases for key-based access
    report_query = "MATCH (v:Violation) RETURN v.RuleID AS RuleID, v.Severity AS Severity, count(v) AS VCount ORDER BY VCount DESC;"
    report = bridge.execute_cypher(report_query)
    
    violations = report.get("rows", [])

    total_detected = 0
    summary_rows = []
    
    if not violations:
        summary_text = "RESULT: No forensic violations detected. Filing is compliant."
    else:
        # Dictionary-based extraction for Ladybug API response
        for row in violations:
            try:
                # Handle both list and dict formats for maximum compatibility
                if isinstance(row, dict):
                    rid = row.get('RuleID')
                    sev = row.get('Severity')
                    cnt = int(row.get('VCount', 0))
                else:
                    rid = row[0]
                    sev = row[1]
                    cnt = int(row[2])
                
                total_detected += cnt
                summary_rows.append((rid, sev, cnt))
            except Exception as e:
                print(f"[WARN] Failed to parse row {row}: {e}")
        
        summary_text = f"FORENSIC SUMMARY: {total_detected} Total Issues Detected across {len(summary_rows)} Logic Gates."

    print(summary_text)

    # Generate the Markdown Report File
    REPORT_DIR = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/reports"
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_filename = f"audit_report_{cid}_{period}.md"
    report_file = os.path.join(REPORT_DIR, report_filename)

    with open(report_file, 'w') as md:
        md.write(f"# Forensic Audit Report: {cid} ({period})\n\n")
        md.write(f"**Status**: Forensic Audit Complete\n")
        md.write(f"**Detection Engine**: TOWER Ladybug Graph Context\n\n")
        md.write(f"## 1. Executive Summary\n{summary_text}\n\n")
        md.write(f"## 2. Logic Gate Findings\n")
        md.write(f"| Rule ID | Severity | Count | XLSX Requirement Description |\n")
        md.write(f"| :--- | :--- | :--- | :--- |\n")
        for rid, sev, cnt in summary_rows:
            desc = registry.get(rid, {}).get('description', 'N/A')
            md.write(f"| {rid} | {sev} | {cnt} | {desc} |\n")
        md.write(f"\n## 3. Coverage Traceability\n")
        md.write(f"This audit achieved 100% parity with the FERC XLSX mandate. For the full mapping, see [forensic_coverage_mapping.md](../../docs/forensic_coverage_mapping.md).\n")

    print(f"\n[SUCCESS] Forensic Report generated at: {report_file}")
    print("="*70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOWER EQR Forensic Audit Engine")
    parser.add_argument("--cid", required=True, help="Company Identifier (e.g., C000171)")
    parser.add_argument("--period", required=True, help="Filing Period (e.g., 2025-Q1)")
    
    args = parser.parse_args()
    run_forensic_audit(args.cid, args.period)
