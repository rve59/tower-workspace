import os
import polars as pl
from pathlib import Path

LAKE_ROOT = Path(f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}/lake")

def get_transaction_sizes():
    results = []
    # Find all transactions.parquet files in the lake
    for tx_path in LAKE_ROOT.glob("**/transactions.parquet"):
        size_bytes = tx_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        
        # Try to find company name in the same directory's ident.parquet
        ident_path = tx_path.parent / "ident.parquet"
        company_name = "Unknown"
        if ident_path.exists():
            try:
                ident_df = pl.read_parquet(ident_path)
                if not ident_df.is_empty():
                    # Check for 'seller_company_name' or 'seller_name' or 'company_name'
                    for col in ["seller_company_name", "seller_name", "company_name"]:
                        if col in ident_df.columns:
                            company_name = ident_df.get_column(col)[0]
                            break
            except Exception:
                pass
        
        # Get CID from path
        # Path is usually lake/CID/YYYY-QQ/tier/transactions.parquet
        parts = tx_path.parts
        cid = "Unknown"
        period = "Unknown"
        for i, part in enumerate(parts):
            if part == "lake" and i + 1 < len(parts):
                cid = parts[i+1]
            if "-" in part and i + 1 < len(parts) and parts[i+1] == "bronze":
                period = part
        
        results.append({
            "CID": cid,
            "Company": company_name,
            "Period": period,
            "Size (MB)": round(size_mb, 2),
            "Path": str(tx_path)
        })
    
    return results

if __name__ == "__main__":
    data = get_transaction_sizes()
    if data:
        df = pl.DataFrame(data)
        print(df)
    else:
        print("No transaction files found.")
