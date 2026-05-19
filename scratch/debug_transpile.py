import polars as pl
from pathlib import Path
import sys

WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel" / "src"))

from tower_kernel.rules.transpiler import CypherTranspiler, RelationalContext

contract_record = {
    "contract_unique_id": "C_CLEAN_001",
    "contract_affiliate": "MAYBE",
}
contract_ldf = pl.LazyFrame([contract_record])

cypher = "MATCH (c:Contracts) WHERE (c.contract_affiliate IS NOT NULL) AND (NOT (c.contract_affiliate IN ['Y', 'N']))"

rel_context = RelationalContext({"Contracts": contract_ldf})

print("Transpiling...")
out_ldf = CypherTranspiler.transpile(cypher, rel_context)
out_df = out_ldf.collect()
print("Result size:", out_df.height)
print("Result data:", out_df)
