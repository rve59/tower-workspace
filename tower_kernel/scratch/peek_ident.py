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
            print(f"Reading inner zip: {inner_name}")
            with m.open(inner_name) as f:
                inner_zip_bytes = io.BytesIO(f.read())
                with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                    ident_files = [n for n in z.namelist() if 'ident' in n.lower()]
                    if ident_files:
                        ident_file = ident_files[0]
                        print(f"Reading ident file: {ident_file}")
                        with z.open(ident_file) as c:
                            df = pl.read_csv(c.read(), n_rows=2)
                            print(df)
                    else:
                        print("No ident file found")
else:
    print(f"Master zip not found at {master_path}")
