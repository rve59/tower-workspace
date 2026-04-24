import zipfile
import io
import re
import os
import shutil
import tempfile
import polars as pl
from pathlib import Path

def build_filing_lookup(master_zip_path: str, output_path: str):
    """
    Scans the master zip archive for EQR sub-zips and extracts company metadata and record counts.
    Uses disk-backed streaming to maintain a low memory footprint (zero RAM buffering for large files).
    """
    print(f"Scanning master archive: {Path(master_zip_path).name}")
    
    filings = []
    
    with zipfile.ZipFile(master_zip_path, 'r') as master:
        sub_zips = [f for f in master.namelist() if f.lower().endswith('.zip')]
        total_zips = len(sub_zips)
        
        for idx, sub_zip_name in enumerate(sub_zips):
            # Status update every 50 files
            if idx % 50 == 0:
                print(f"Progress: {idx}/{total_zips} filings processed...")
                
            try:
                # 1. Stream the sub-zip from master to a temporary file on disk
                with master.open(sub_zip_name) as sub_file_stream:
                    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_sub:
                        shutil.copyfileobj(sub_file_stream, tmp_sub)
                        tmp_sub_path = tmp_sub.name
                
                try:
                    with zipfile.ZipFile(tmp_sub_path) as sub_zip:
                        internal_files = sub_zip.namelist()
                        
                        # A. Extract name metadata from _ident.csv (small, memory is fine)
                        ident_file = next((f for f in internal_files if '_ident.csv' in f.lower()), None)
                        company_name = "Unknown"
                        period = "000000"
                        
                        if ident_file:
                            with sub_zip.open(ident_file) as f:
                                # Quick read of first few lines to get the name
                                ident_df = pl.read_csv(f, n_rows=1, ignore_errors=True)
                                if not ident_df.is_empty():
                                    # Fallback to regex if CSV structure is weird
                                    match = re.search(r'\d{6}_(.+)_ident\.csv', ident_file, re.IGNORECASE)
                                    company_name = match.group(1).replace('_', ' ') if match else "Unknown"
                                    period = ident_file[:6]

                        # B. Extract record count from _transactions.csv
                        tx_file = next((f for f in internal_files if '_transactions.csv' in f.lower()), None)
                        row_count = 0
                        if tx_file:
                            # Stream the CSV to a temporary file for Polars scan
                            with sub_zip.open(tx_file) as csv_stream:
                                with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp_csv:
                                    shutil.copyfileobj(csv_stream, tmp_csv)
                                    tmp_csv_path = tmp_csv.name
                            
                            try:
                                # Fast count via lazy scanning (low memory)
                                row_count = pl.scan_csv(tmp_csv_path, infer_schema_length=0).select(pl.len()).collect().item()
                            finally:
                                if os.path.exists(tmp_csv_path):
                                    os.remove(tmp_csv_path)

                        # Parse period metadata
                        year = int(period[:4]) if len(period) >= 4 and period[:4].isdigit() else 0
                        month = int(period[4:6]) if len(period) >= 6 and period[4:6].isdigit() else 0
                        quarter = (month - 1) // 3 + 1 if month > 0 else 0
                        
                        # Patterns for company_id extraction from filename
                        id_match = re.search(r'CSV_\d{4}_Q\d_(\d+)_', sub_zip_name)
                        company_id = id_match.group(1) if id_match else "unknown"
                        
                        filings.append({
                            "sub_zip_name": sub_zip_name,
                            "company_id": company_id,
                            "company_name": company_name,
                            "period": period,
                            "year": year,
                            "quarter": quarter,
                            "year_quarter": f"{year}Q{quarter}",
                            "row_count": row_count
                        })
                        
                finally:
                    # Clean up the temporary sub-zip file immediately
                    if os.path.exists(tmp_sub_path):
                        os.remove(tmp_sub_path)
                        
            except Exception as e:
                print(f"Warning: Failed to process {sub_zip_name}: {e}")

    if not filings:
        print("Error: No filings discovered.")
        return

    # Create Lookup Table
    df = pl.DataFrame(filings)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.write_parquet(output_path)
    print(f"Discovery complete. Processed {len(filings)} entities.")
    total_rows_global = df["row_count"].sum()
    print(f"Global record count: {total_rows_global:,}")
    print(f"Lookup table saved to: {output_path}")

if __name__ == "__main__":
    MASTER_ZIP = "/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower.docs/FERC EQR SAMPLES/CSV_2025_Q1.zip"
    OUTPUT = "data/lake/filing_lookup.parquet"
    build_filing_lookup(MASTER_ZIP, OUTPUT)
