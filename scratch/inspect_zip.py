import os
import zipfile
import io

master_path = "./tower_kernel/data/historic/CSV_2025_Q1.zip"
with zipfile.ZipFile(master_path, 'r') as z_master:
    inner_name = z_master.namelist()[0]
    with z_master.open(inner_name) as inner_f:
        with zipfile.ZipFile(io.BytesIO(inner_f.read())) as z:
            ident_file = [n for n in z.namelist() if n.endswith('_ident.CSV')][0]
            with z.open(ident_file) as f:
                header = f.readline().decode('utf-8')
                print(f"Header of {ident_file}:")
                print(header)
                first_row = f.readline().decode('utf-8')
                print("First row:")
                print(first_row)
