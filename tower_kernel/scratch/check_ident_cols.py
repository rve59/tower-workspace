import zipfile
import io
import polars as pl
import os

master_path = 'tower_kernel/data/historic/CSV_2025_Q1.zip'

if os.path.exists(master_path):
    with zipfile.ZipFile(master_path, 'r') as m:
        inner_names = m.namelist()
        if inner_names:
            inner_name = inner_names[0]
            with m.open(inner_name) as f:
                inner_zip_bytes = io.BytesIO(f.read())
                with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                    idnt = [n for n in z.namelist() if 'ident' in n.lower()][0]
                    with z.open(idnt) as cf:
                        df = pl.read_csv(cf.read(), n_rows=1)
                        print("Columns in ident.csv:")
                        for c in df.columns:
                            print(f" - {c}")
else:
    print(f"Master zip not found at {master_path}")
