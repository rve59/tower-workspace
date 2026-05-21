
import polars as pl
import os

def check_schema():
    # Try to find an ident.parquet file
    path = f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}/parquets/C000171/2023Q3/ident.parquet'
    # Wait, the ls output didn't show full paths. Let me find one.
    # I'll just check the root of parquets if it exists
    
    # Based on the ls output, it seems they are in subdirectories.
    # I'll use find to get a real path
    for root, dirs, files in os.walk(f"{os.environ.get('TOWER_DATA_ROOT', f"{os.environ.get('TOWER_DATA_ROOT', 'tower_kernel/data')}')}'):
        if 'ident.parquet' in files:
            p = os.path.join(root, 'ident.parquet')
            print(f"Checking {p}")
            df = pl.scan_parquet(p)
            print("Columns:", df.columns)
            break

if __name__ == "__main__":
    check_schema()
