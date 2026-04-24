import zipfile
import io
import polars as pl
import os

master_path = 'tower_kernel/data/historic/CSV_2025_Q1.zip'
inner_name = 'CSV_2025_Q1_6076115_1649014.ZIP' # Puget Sound Energy

if os.path.exists(master_path):
    with zipfile.ZipFile(master_path, 'r') as m:
        print(f"Opening inner zip: {inner_name}")
        with m.open(inner_name) as f:
            inner_zip_bytes = io.BytesIO(f.read())
            with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                files = z.namelist()
                print(f"Files found in inner zip: {files}")
                
                # Check transactions
                tx_match = [n for n in files if 'transaction' in n.lower()]
                if tx_match:
                    tx_file = tx_match[0]
                    print(f"Reading FULL Transaction file: {tx_file}")
                    with z.open(tx_file) as txf:
                        content = txf.read()
                        print(f"Total file size: {len(content)} bytes")
                        
                        # Attempt reading with polars
                        try:
                            # Try different encodings
                            df = pl.read_csv(io.BytesIO(content), ignore_errors=True)
                            print(f"Polars read SUCCESS. Shape: {df.shape}")
                        except Exception as e:
                            print(f"Polars read failed: {e}")
                else:
                    print("No transactions file found.")

else:
    print("Master zip not found")
