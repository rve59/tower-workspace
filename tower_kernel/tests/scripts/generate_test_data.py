import polars as pl
import random
from pathlib import Path
from datetime import datetime, timedelta

def generate_erp_data(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Sellers
    sellers = pl.DataFrame([
        {"seller_id": "S100", "name": "Vibes Energy Corp", "tax_id": "TX-001"},
        {"seller_id": "S200", "name": "Antigravity Power", "tax_id": "TX-002"}
    ])
    sellers.write_csv(output_dir / "erp_sellers.csv")
    
    # 2. Contracts
    contracts = pl.DataFrame([
        {"contract_id": "CTR-001", "seller_id": "S100", "customer_name": "MegaGrid", "start_date": "2024-01-01", "end_date": "2024-12-31"},
        {"contract_id": "CTR-002", "seller_id": "S200", "customer_name": "CityPower", "start_date": "2024-02-01", "end_date": "2025-01-31"}
    ])
    contracts.write_csv(output_dir / "erp_contracts.csv")
    
    # 3. Terms
    terms = pl.DataFrame([
        {"term_id": "TRM-01", "contract_id": "CTR-001", "product_code": "ENERGY", "unit_price": 55.5, "qty_limit": 100000.0},
        {"term_id": "TRM-02", "contract_id": "CTR-002", "product_code": "CAPACITY", "unit_price": 1200.0, "qty_limit": 500.0}
    ])
    terms.write_csv(output_dir / "erp_terms.csv")
    
    # 4. Transactions (Large set simulation)
    num_tx = 1000
    dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(num_tx)]
    
    tx_id = [f"TX-{i:04d}" for i in range(num_tx)]
    term_ids = ["TRM-01", "TRM-02"]
    selected_terms = [random.choice(term_ids) for _ in range(num_tx)]
    quantities = [round(random.uniform(5, 50), 2) for _ in range(num_tx)]
    
    txs = pl.DataFrame({
        "tx_id": tx_id,
        "term_id": selected_terms,
        "tx_date": [d.strftime("%Y-%m-%d %H:%M:%S") for d in dates],
        "quantity": quantities,
    })
    
    # Join with terms to get price for calculating total_charge
    txs = txs.join(terms.select(["term_id", "unit_price"]), on="term_id")
    txs = txs.with_columns(
        (pl.col("quantity") * pl.col("unit_price")).round(2).alias("total_charge")
    ).drop("unit_price")
    
    txs.write_csv(output_dir / "erp_transactions.csv")
    
    print(f"Generated ERP test data in {output_dir}")

if __name__ == "__main__":
    generate_erp_data(Path("tower_kernel/tests/data/erp_dump"))
