import os
import polars as pl
from tower_kernel.rules.transpiler import CypherTranspiler, RelationalContext
import json

def debug_transpilation():
    t_path = f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}/lake/C000041/2025-Q1/silver/transactions.parquet"
    c_path = f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}/lake/C000041/2025-Q1/silver/contracts.parquet"
    
    t_ldf = pl.scan_parquet(t_path)
    c_ldf = pl.scan_parquet(c_path)
    
    rel_context = RelationalContext({
        "Transactions": t_ldf,
        "Contracts": c_ldf
    })
    
    cypher = "MATCH (t:Transactions) WHERE NOT EXISTS { MATCH (c:Contracts) WHERE t.contract_service_agreement = c.contract_service_agreement_id AND t.product_name = c.product_name } MERGE (v:Violation) MERGE (v);"
    
    print("Transpiling...")
    try:
        violation_ldf = CypherTranspiler.transpile(cypher, rel_context)
        print("Executing...")
        violations = violation_ldf.collect()
        print(f"Violations: {violations.height}")
        if violations.height > 0:
            print(violations.head(5))
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    debug_transpilation()
