import polars as pl
import os
import datetime
from pathlib import Path
from tower_kernel import config
from tower_kernel.rules.eqr import run_benchmarked_validation
from tower_kernel.services.registry_mirror import RegistryMirrorService
from tower_kernel.services.diagnostic import DiagnosticService

# Setup registry and draft
RegistryMirrorService.bootstrap_sample_data()
temp_csv = str(config.REGISTRY_ROOT / "temp_update.csv")
with open(temp_csv, "w") as f:
    f.write("CID,Organization_Name,effective_start_date,effective_end_date\n")
    f.write("TEST_CID,Official Legal Name,2020-01-01,\n")

RegistryMirrorService.import_registry(temp_csv)
os.remove(temp_csv)

# Case 2: CID correct, but Name Mismatch
cid = "TEST_CID"
seller_name = "Mismatched Name Ltd"
df = pl.DataFrame({
    "transaction_unique_id": ["T1"],
    "contract_unique_id": ["C1"],
    "seller_company_name": [seller_name],
    "product_name": ["ENERGY"],
    "rate_units": ["$/MWH"],
    "total_transaction_charge": [100.0],
    "total_transmission_charge": [0.0],
    "transaction_quantity": [1.0],
    "price": [100.0],
    "transaction_begin_date": [datetime.date(2024, 1, 1)],
    "transaction_end_date": [datetime.date(2024, 1, 2)],
    "class_name": ["OS"],
    "term_name": ["S"],
    "increment_name": ["H"],
    "increment_peaking_name": ["P"],
    "time_zone": ["PST"],
    "point_of_delivery_balancing_authority": ["PJM"],
    "point_of_delivery_specific_location": ["HUB"],
    "ferc_tariff_reference": ["TARIFF"],
    "trade_date": [datetime.date(2024, 1, 1)],
    "type_of_rate": ["F"],
    "standardized_price": [100.0],
    "standardized_quantity": [1.0],
    "source_filename": ["test.zip"],
    "source_row_index": [1]
})

DRAFT_DIR = str(config.DATA_ROOT / "workspace" / "drafts" / "user_id=test" / "session_id=registry_test" / "draft.parquet")
from tower_kernel.ingest.streaming import write_parquet_with_metadata
write_parquet_with_metadata(
    df, 
    Path(DRAFT_DIR), 
    cid, 
    "Test Common Name",
    extra_metadata={"year": "2024", "quarter": "1"}
)

ldf = pl.scan_parquet(DRAFT_DIR)
registry_ldf = RegistryMirrorService.get_mirror_ldf()

print("REGISTRY:")
print(registry_ldf.collect())

print("TRANSACTIONS:")
from tower_kernel.rules.eqr import _normalize_schema
normalized_t = _normalize_schema(ldf, metadata={"cid": cid, "year": "2024", "quarter": "1"})
print(normalized_t.collect())

# Let's test the transpiler explicitly
from tower_kernel.rules.transpiler import CypherTranspiler, RelationalContext
rel_context = RelationalContext({
    "Transactions": normalized_t,
    "Registry": registry_ldf
})

cypher = "MATCH (t:Transactions), (r:Registry) WHERE t.seller_cid = r.cid AND t.seller_company_name <> r.legal_name"
try:
    ldf_res = CypherTranspiler.transpile(cypher, rel_context)
    print("TRANSPILED DF:")
    print(ldf_res.collect())
except Exception as e:
    print("TRANSPILATION ERROR:", e)
