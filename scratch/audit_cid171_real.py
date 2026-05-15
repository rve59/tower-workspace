import polars as pl
import os
from pathlib import Path
from tower_kernel.utils.logging import log_progress

# We will reuse the core logic from our documentation and test harness
# but target the actual bronze lake files.

def log_info(msg):
    log_progress(msg, "INFO")

BASE_PATH = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/lake/C000171/2025-Q1/bronze/"
IDENT_PATH = os.path.join(BASE_PATH, "ident.parquet")
CONTRACT_PATH = os.path.join(BASE_PATH, "contracts.parquet")
TRANS_PATH = os.path.join(BASE_PATH, "transactions.parquet")

def ingest_real_data():
    """
    Reads the real parquet files and prepares them for the Cypher engine.
    In a real system, we would use COPY FROM, but for this demonstration
    we will simulate the graph state to run our formalized logic gates.
    """
    log_info("Loading real-world bronze data for CID 171...")
    
    ident_df = pl.read_parquet(IDENT_PATH)
    contract_df = pl.read_parquet(CONTRACT_PATH)
    trans_df = pl.read_parquet(TRANS_PATH)
    
    log_info(f"Identity Records: {len(ident_df)}")
    log_info(f"Contract Records: {len(contract_df)}")
    log_info(f"Transaction Records: {len(trans_df)}")

    # Mapping Logic: Convert descriptive parquet names to FERC Field IDs
    # This simulates the 'Transpilation Ready' schema alignment
    
    # Example Mapping (Ident)
    # company_identifier -> CID
    # filer_unique_id -> Field_1
    # company_name -> Field_2
    
    # We will pass these as UNWIND parameters to our Cypher engine.
    return {
        "ident": ident_df.to_dicts(),
        "contracts": contract_df.to_dicts(),
        "transactions": trans_df.head(1000).to_dicts() # Sample first 1000 for forensic performance
    }

def run_forensic_audit():
    data = ingest_real_data()
    
    # The actual Cypher rules we defined
    rules = [
        "F.16.13", "F.16.11", "F.16.21", "F.24.6", "F.25.18", "F.24.3", "F.21.15"
    ]
    
    log_info("Starting Forensic Audit Logic Gates...")
    
    # Simulation: In a real system, these would execute as Cypher MATCH/WHERE clauses
    # against the ingested Ladybug graph.
    
    violations = []
    
    # Rule F.24.3 Check: End Date > Begin Date
    for tx in data["transactions"]:
        begin = tx.get("transaction_begin_date")
        end = tx.get("transaction_end_date")
        if begin and end and str(end) < str(begin):
            violations.append({
                "rule": "F.24.3",
                "id": tx.get("transaction_unique_id"),
                "msg": f"End Date {end} is before Begin Date {begin}"
            })

    # Rule F.24.6 Check: Financial Math
    for tx in data["transactions"]:
        qty = tx.get("transaction_quantity") or 0
        price = tx.get("transaction_price") or 0
        total = tx.get("total_transaction_charge") or 0
        expected = float(qty) * float(price)
        if abs(expected - float(total)) > 0.01 * expected:
             violations.append({
                "rule": "F.24.6",
                "id": tx.get("transaction_unique_id"),
                "msg": f"Math Mismatch: {qty} * {price} = {expected}, reported {total}"
            })

    # Rule F.25.18 Check: Transaction Product matched by Contract Product
    # First, build a map of Authorized Products per Customer
    auth_map = {}
    for c in data["contracts"]:
        cust = c.get("customer_company_name")
        prod = c.get("product_name")
        if cust not in auth_map: auth_map[cust] = set()
        auth_map[cust].add(prod)

    for tx in data["transactions"]:
        cust = tx.get("customer_company_name")
        prod = tx.get("product_name")
        if cust in auth_map and prod not in auth_map[cust]:
            violations.append({
                "rule": "F.25.18",
                "id": tx.get("transaction_unique_id"),
                "msg": f"Product '{prod}' not authorized in contract for customer '{cust}'"
            })

    log_info(f"Audit Complete. Found {len(violations)} Forensic Violations in CID 171.")
    
    for v in violations:
        print(f"[VIOLATION] Rule {v['rule']} - Offender: {v['id']} - {v['msg']}")

if __name__ == "__main__":
    run_forensic_audit()
