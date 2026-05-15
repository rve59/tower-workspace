import kuzu
import os
import shutil
from pathlib import Path

# Paths to the real CID 171 data
BASE_PATH = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/lake/C000171/2025-Q1/bronze/"
IDENT_PATH = os.path.join(BASE_PATH, "ident.parquet")
CONTRACT_PATH = os.path.join(BASE_PATH, "contracts.parquet")
TRANS_PATH = os.path.join(BASE_PATH, "transactions.parquet")

# Initialize a clean local graph environment
DB_PATH = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/scratch/audit_db"
if os.path.exists(DB_PATH):
    shutil.rmtree(DB_PATH)

db = kuzu.Database(DB_PATH)
conn = kuzu.Connection(db)

def execute(query, params=None):
    print(f"\n[CYPHER] {query}")
    try:
        if params:
            result = conn.execute(query, params)
        else:
            result = conn.execute(query)
        
        # Convert to list of dicts for reporting
        rows = []
        while result.has_next():
            rows.append(result.get_next())
        return rows
    except Exception as e:
        print(f"[ERROR] {e}")
        return []

# 1. Define Schema (Actual DDL)
# We map the descriptive Parquet columns to the Node properties
print("--- INITIALIZING FORENSIC GRAPH SCHEMA ---")

execute("""
CREATE NODE TABLE IDData(
    filer_unique_id STRING,
    company_name STRING,
    company_identifier STRING,
    report_to_index STRING,
    CID STRING,
    PRIMARY KEY (filer_unique_id)
);
""")

execute("""
CREATE NODE TABLE ContractTerms(
    contract_unique_id STRING,
    seller_company_name STRING,
    customer_company_name STRING,
    product_name STRING,
    rate_units STRING,
    actual_termination_date STRING,
    PRIMARY KEY (contract_unique_id)
);
""")

execute("""
CREATE NODE TABLE TransactionData(
    transaction_unique_id STRING,
    customer_company_name STRING,
    product_name STRING,
    transaction_quantity DOUBLE,
    transaction_price DOUBLE,
    total_transaction_charge DOUBLE,
    transaction_begin_date STRING,
    transaction_end_date STRING,
    PRIMARY KEY (transaction_unique_id)
);
""")

# 2. Ingest Data (Actual COPY - ZERO COPY/IN-PLACE)
print("\n--- INGESTING BRONZE LAKE DATA (READING IN-PLACE) ---")

execute(f"COPY IDData FROM '{IDENT_PATH}';")
execute(f"COPY ContractTerms FROM '{CONTRACT_PATH}';")
execute(f"COPY TransactionData FROM '{TRANS_PATH}';")

# 3. Create Logical Relationships (The 'Knitting' phase)
# We link transactions to their authorizing contracts
print("\n--- KNITTING TRANSACTION-TO-CONTRACT RELATIONS ---")
execute("CREATE REL TABLE AUTHORIZED_BY(FROM TransactionData TO ContractTerms);")

# Simple join on product and customer (as defined in F.25.18 logic)
execute("""
MATCH (t:TransactionData), (c:ContractTerms)
WHERE t.customer_company_name = c.customer_company_name
  AND t.product_name = c.product_name
CREATE (t)-[:AUTHORIZED_BY]->(c)
""")

# 4. Execute ACTUAL Forensic Rules
print("\n--- EXECUTING ACTUAL FORENSIC VALIDATION RULES ---")

# Rule F.24.6: Financial Integrity (Price * Quantity = Total Charge)
# Actual Cypher from documentation (adapted for Parquet column names)
f246_results = execute("""
MATCH (t:TransactionData)
WHERE abs((t.transaction_price * t.transaction_quantity) - t.total_transaction_charge) > 1.0
RETURN t.transaction_unique_id AS ID, 
       t.total_transaction_charge AS Reported, 
       (t.transaction_price * t.transaction_quantity) AS Calculated
LIMIT 10
""")

print(f"\n[RULE F.24.6] Found {len(f246_results)} Violations (Sample shown):")
for r in f246_results:
    print(f"  - Transaction {r[0]}: Expected {r[2]:.2f}, Reported {r[1]:.2f}")

# Rule F.25.18: Product Authorization (Transactions with no AUTHORIZED_BY relation)
# This is a POWERFUL graph check: "Find any transaction that does NOT point to a valid contract"
f2518_results = execute("""
MATCH (t:TransactionData)
WHERE NOT (t)-[:AUTHORIZED_BY]->(:ContractTerms)
RETURN t.transaction_unique_id AS ID, t.product_name AS Product, t.customer_company_name AS Customer
LIMIT 10
""")

print(f"\n[RULE F.25.18] Found {len(f2518_results)} Unauthorized Transactions (Sample shown):")
for r in f2518_results:
    print(f"  - Transaction {r[0]}: Product '{r[1]}' is NOT AUTHORIZED for customer '{r[2]}'")

# Rule F.24.3: Temporal Sequence
f243_results = execute("""
MATCH (t:TransactionData)
WHERE t.transaction_end_date < t.transaction_begin_date
RETURN t.transaction_unique_id AS ID, t.transaction_begin_date AS Begin, t.transaction_end_date AS End
""")

print(f"\n[RULE F.24.3] Found {len(f243_results)} Temporal Violations.")

print("\n--- FORENSIC AUDIT COMPLETE ---")
