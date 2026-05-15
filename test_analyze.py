from tower_kernel.services.diagnostic import DiagnosticService
from tower_kernel import config
import os
os.environ["TOWER_GEMINI_MODEL"] = "gemini-3.1-flash-lite-preview"
try:
    parquet_path = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/data/lake/C000171/2025-Q1/bronze/transactions.parquet"
    res = DiagnosticService.analyze_failure_set_with_ai(parquet_path, "F.17.13")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
