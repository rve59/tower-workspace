import polars as pl
from pathlib import Path

INDEX_PATH = Path("tower_kernel/data/master/registry/discovery_index.parquet")

def check_index():
    if not INDEX_PATH.exists():
        print("Discovery index not found.")
        return
    
    df = pl.read_parquet(INDEX_PATH)
    print(df)

if __name__ == "__main__":
    check_index()
