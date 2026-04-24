import zipfile
import io
import polars as pl
import os

master_path = 'tower_kernel/data/historic/CSV_2025_Q1.zip'
results = []

if os.path.exists(master_path):
    print(f"Scanning {master_path} for WA state entities (including size & tech_id)...")
    with zipfile.ZipFile(master_path, 'r') as m:
        inner_zips = [n for n in m.namelist() if n.endswith(".ZIP")]
        
        for i, inner_name in enumerate(inner_zips):
            try:
                # Get ZIP info for size
                zinfo = m.getinfo(inner_name)
                f_size_mb = zinfo.file_size / 1024 / 1024
                
                # Parse tech_id from filename
                # Pattern: CSV_{Y}_Q{Q}_{CID}_{TECHID}.ZIP
                tech_id = inner_name.replace(".ZIP", "").split("_")[-1]
                
                with m.open(inner_name) as f:
                    inner_zip_bytes = io.BytesIO(f.read())
                    with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                        ident_files = [n for n in z.namelist() if 'ident' in n.lower()]
                        if not ident_files:
                            continue
                        
                        with z.open(ident_files[0]) as id_f:
                            df = pl.read_csv(id_f.read(), ignore_errors=True)
                            
                            if "contact_state" in df.columns:
                                wa_filings = df.filter(pl.col("contact_state").str.to_uppercase() == "WA")
                                if wa_filings.height > 0:
                                    company_name = df.get_column("company_name")[0] if "company_name" in df.columns else "Unknown"
                                    cid = df.get_column("company_identifier")[0] if "company_identifier" in df.columns else "Unknown"
                                    results.append({
                                        "cid": cid,
                                        "size_mb": f"{f_size_mb:.2f} MB",
                                        "tech_id": tech_id,
                                        "name": company_name
                                    })
            except Exception as e:
                continue

    # De-duplicate by CID (keeping first encounter per domain logic)
    seen_cids = set()
    unique_results = []
    for r in results:
        if r['cid'] not in seen_cids:
            unique_results.append(r)
            seen_cids.add(r['cid'])

    print("\n| CID | File Size | Technical ID | Entity Name |")
    print("| :--- | :--- | :--- | :--- |")
    for r in sorted(unique_results, key=lambda x: x['name']):
        print(f"| **{r['cid']}** | {r['size_mb']} | `{r['tech_id']}` | {r['name']} |")

else:
    print(f"Master zip not found at {master_path}")
