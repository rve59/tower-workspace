import zipfile
import io
import polars as pl
from tower_kernel.ingest.schema_compiler import TRANSACTION_COMPILER

master_path = 'tower_kernel/data/historic/CSV_2025_Q1.zip'
inner_name = 'CSV_2025_Q1_6076115_1649014.ZIP'

with zipfile.ZipFile(master_path, 'r') as m:
    with m.open(inner_name) as f:
        inner_zip_bytes = io.BytesIO(f.read())
        with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
            tx_files = [n for n in z.namelist() if 'transaction' in n.lower()]
            if tx_files:
                tx_file = tx_files[0]
                with z.open(tx_file) as cf:
                    df_raw = pl.read_csv(cf.read(), n_rows=1)
                    csv_cols = sorted(df_raw.columns)
                    expected_cols = sorted(list(TRANSACTION_COMPILER["schema"].keys()))
                    
                    print(f"CSV Columns: {csv_cols}")
                    print(f"Expected Columns: {expected_cols}")
                    
                    missing = [c for c in expected_cols if c not in csv_cols]
                    extra = [c for c in csv_cols if c not in expected_cols]
                    
                    print(f"Missing in CSV: {missing}")
                    print(f"Extra in CSV: {extra}")
                    
                    # Test read with expected schema
                    try:
                        cf.seek(0)
                        df_test = pl.read_csv(cf.read(), schema_overrides=TRANSACTION_COMPILER["schema"], ignore_errors=True)
                        print(f"Test Read Shape: {df_test.shape}")
                    except Exception as e:
                        print(f"Test Read Error: {e}")
