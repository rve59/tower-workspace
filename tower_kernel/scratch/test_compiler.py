from tower_kernel.ingest.schema_compiler import IDENT_COMPILER, TRANSACTION_COMPILER
import polars as pl

print("--- IDENT SCHEMA ---")
print(IDENT_COMPILER["schema"])
print("\n--- IDENT RENAME ---")
print(IDENT_COMPILER["rename"])

print("\n--- TRANSACTION META ---")
for k, v in TRANSACTION_COMPILER["meta"].items():
    print(f"{k}: {v}")
