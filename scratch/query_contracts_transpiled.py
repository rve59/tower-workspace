import polars as pl
from pathlib import Path

def query_authorized_products():
    # 1. Path to the C000041 2025-Q1 bronze data
    lake_path = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/lake/C000041/2025-Q1/bronze")
    contracts_file = lake_path / "contracts.parquet"

    if not contracts_file.exists():
        print(f"Error: {contracts_file} not found.")
        return

    # 2. Transpiled Logic: 
    # MATCH (c:Contracts) 
    # WHERE c.contract_service_agreement_id = 'Service Agreement No 13' 
    # RETURN c.product_name AS AuthorizedProduct

    # Transpilation Phase:
    # MATCH (c:Contracts) -> Scan Parquet
    # WHERE ... -> .filter(pl.col('contract_service_agreement_id') == 'Service Agreement No 13')
    # RETURN ... -> .select(pl.col('product_name').alias('AuthorizedProduct'))

    ldf = pl.scan_parquet(contracts_file)
    
    result = (
        ldf
        .filter(pl.col("contract_service_agreement_id") == "Service Agreement No 13")
        .select(pl.col("product_name").alias("AuthorizedProduct"))
        .unique() # Cypher RETURN usually implies distinct set if it was RETURN DISTINCT, but here we'll keep it for clarity
        .collect()
    )

    print(f"Query Results for 'Service Agreement No 13':")
    if result.height == 0:
        print("  - No authorized products found for this contract ID.")
    else:
        print(result)

if __name__ == "__main__":
    query_authorized_products()
