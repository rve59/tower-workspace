import polars as pl
from tower_kernel.rules.eqr import run_benchmarked_validation
path = '/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/lake/C000171/bronze/transactions.parquet'
ldf = pl.scan_parquet(path)
try:
    df, stats = run_benchmarked_validation(ldf)
    print("SUCCESS")
except Exception as e:
    print("ERROR MSG:", str(e))
