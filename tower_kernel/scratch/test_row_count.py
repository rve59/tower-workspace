import polars as pl
import time
import os
import tempfile
import zipfile
import shutil

MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"

def test_streaming_count():
    with zipfile.ZipFile(MASTER_ZIP, 'r') as master:
        # Pick a medium-sized sub-zip
        sub_zip_name = "CSV_2025_Q1_6438859_1713060.ZIP"
        print(f"Testing: {sub_zip_name}")
        
        with master.open(sub_zip_name) as sub_file:
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_sub:
                shutil.copyfileobj(sub_file, tmp_sub)
                tmp_sub_path = tmp_sub.name
        
        try:
            with zipfile.ZipFile(tmp_sub_path) as sub_zip:
                tx_file = next((f for f in sub_zip.namelist() if "_transactions.csv" in f.lower()), None)
                if tx_file:
                    with sub_zip.open(tx_file) as csv_in:
                        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
                            shutil.copyfileobj(csv_in, tmp_csv)
                            tmp_csv_path = tmp_csv.name
                    
                    try:
                        count = pl.scan_csv(tmp_csv_path, infer_schema_length=0).select(pl.len()).collect().item()
                        print(f"Row count: {count:,}")
                    finally:
                        if os.path.exists(tmp_csv_path):
                            os.remove(tmp_csv_path)
        finally:
            if os.path.exists(tmp_sub_path):
                os.remove(tmp_sub_path)

if __name__ == "__main__":
    start = time.perf_counter()
    test_streaming_count()
    print(f"Time: {time.perf_counter() - start:.2f}s")
