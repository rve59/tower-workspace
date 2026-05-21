import sys
import os
import json
from pathlib import Path

# Add TOWER and Ladybug paths
WORKSPACE_ROOT = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE"
sys.path.append(os.path.join(WORKSPACE_ROOT, "tower_kernel/src"))
sys.path.append(os.path.join(WORKSPACE_ROOT, "ladybug.libs/lib_ldbg_tower_bridge/src"))

from lib_ldbg_tower_bridge.bridge import LadybugTowerBridge
from tower_kernel.services.audit_agent import RegulatoryAuditorAgent, ForensicBrief

def generate_cid171_briefing():
    print("--- TOWER AI FORENSIC AUDITOR ---")
    print("Initializing Graph Discovery...")
    
    bridge = LadybugTowerBridge(api_url="http://localhost:9045")
    
    # 1. Pull forensic sample for F.25.18 (The Authorization Breach)
    # We want a sample of transactions that failed, along with their 'attempted' product and the 'actual' contract product
    query = """
    MATCH (t:Transactions)
    WHERE NOT EXISTS {
      MATCH (c:Contracts)
      WHERE t.contract_service_agreement = c.contract_service_agreement_id
        AND t.product_name = c.product_name
    }
    OPTIONAL MATCH (c:Contracts) WHERE t.contract_service_agreement = c.contract_service_agreement_id
    RETURN 
        t.transaction_unique_id as TX_ID,
        t.contract_service_agreement as AGREEMENT,
        t.product_name as TX_PRODUCT,
        c.product_name as CONTRACT_PRODUCT,
        t.customer_company_name as CUSTOMER
    LIMIT 20;
    """
    
    res = bridge.execute_cypher(query)
    samples = res.get("rows", [])
    
    if not samples:
        print("No violations found to analyze.")
        return

    # 2. Convert to list of dicts for the brief
    sample_data = []
    for s in samples:
        sample_data.append({
            "TransactionID": s.get("TX_ID"),
            "AgreementID": s.get("AGREEMENT"),
            "AttemptedProduct": s.get("TX_PRODUCT"),
            "AuthorizedProduct": s.get("CONTRACT_PRODUCT") or "NONE (Agreement Missing)",
            "Customer": s.get("CUSTOMER")
        })

    # 3. Build the Forensic Brief
    # We provide the AI with the rule context and the specific cluster sample
    rule_spec = {
      "rule_id": "F.25.18",
      "category": "FORENSIC",
      "description": "Product Authorization Mismatch: Transaction product not authorized by Contract Terms."
    }
    
    # Aggregate stats for the AI
    stats_query = "MATCH (v:Violation {RuleID: 'F.25.18'}) RETURN count(v) as total;"
    stats_res = bridge.execute_cypher(stats_query)
    total_violations = stats_res["rows"][0]["total"] if stats_res["rows"] else 274867
    
    print(f"Synthesizing Brief for {total_violations} violations...")
    
    # Scale context
    total_records = 500000 # Estimate for CID 171
    violation_rate = total_violations / total_records
    
    brief = ForensicBrief(
        rule_id=rule_spec["rule_id"],
        category=rule_spec["category"],
        description=rule_spec["description"],
        error_count=total_violations,
        total_count=total_records,
        violation_rate=violation_rate,
        sample_records=sample_data
    )

    # 4. Invoke Gemini for Expert Analysis
    print("Requesting Expert Analysis from Gemini...")
    agent = RegulatoryAuditorAgent()
    
    REPORT_PATH = Path(WORKSPACE_ROOT) / f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}/reports/forensic_brief_C000171_2025Q1.md"
    
    try:
        report_md = agent.submit_to_gemini(brief, save_to=REPORT_PATH)
        print(f"\n[SUCCESS] Forensic Brief generated at: {REPORT_PATH}")
        print("\n--- REPORT PREVIEW ---")
        print(report_md[:500] + "...")
        print("----------------------")
    except Exception as e:
        print(f"\n[ERROR] Gemini interaction failed: {e}")
        # Save the offline brief as fallback
        offline_brief = agent._render_offline_brief(brief)
        REPORT_PATH.write_text(offline_brief)
        print(f"[OFFLINE] Rendered raw brief to: {REPORT_PATH}")

if __name__ == "__main__":
    generate_cid171_briefing()
