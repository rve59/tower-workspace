import polars as pl
from pathlib import Path
import os

INDEX_PATH = Path("tower_kernel/data/master/registry/discovery_index.parquet")
LAKE_ROOT = Path("tower_kernel/data/lake")

COMPANIES = [
    "Avista", "Puget Sound Energy", "PacifiCorp", "Cascade Natural Gas",
    "Bonneville Power", "Western Power Pool", "Shell Energy", "Powerex",
    "Energy Northwest", "The Energy Authority", "Public Generating Pool",
    "Columbia Basin Hydropower", "Sagebrush ESS", "Badger Mountain Solar",
    "Washington 10 Storage", "Lund Hill Solar", "Great Bend Solar",
    "Wautoma Solar", "Hopberry Solar", "Horse Heaven Solar",
    "Clearview Solar", "Tono Solar"
]

def find_company_data():
    if not INDEX_PATH.exists():
        return "Index not found"
    
    df = pl.read_parquet(INDEX_PATH)
    
    results = []
    for search_name in COMPANIES:
        # Case-insensitive search in legal_name
        matches = df.filter(pl.col("legal_name").str.contains(f"(?i){search_name}"))
        
        if matches.is_empty():
            results.append({"Company": search_name, "Status": "Not in Index"})
            continue
        
        # Get unique CIDs for this search name
        cids = matches.select("cid").unique().get_column("cid").to_list()
        
        found_in_lake = False
        for cid in cids:
            cid_path = LAKE_ROOT / cid
            if cid_path.exists():
                # Check for transactions and contracts in any subfolder
                for tx_path in cid_path.glob("**/transactions.parquet"):
                    found_in_lake = True
                    tx_size = tx_path.stat().st_size / (1024 * 1024)
                    
                    # Count records
                    tx_df = pl.scan_parquet(tx_path)
                    tx_count = tx_df.select(pl.len()).collect().item()
                    
                    # Check contracts
                    ct_path = tx_path.parent / "contracts.parquet"
                    ct_size = 0.0
                    ct_count = 0
                    if ct_path.exists():
                        ct_size = ct_path.stat().st_size / (1024 * 1024)
                        ct_df = pl.scan_parquet(ct_path)
                        ct_count = ct_df.select(pl.len()).collect().item()
                    
                    results.append({
                        "Company": search_name,
                        "Matched Name": matches.filter(pl.col("cid") == cid)["legal_name"][0],
                        "CID": cid,
                        "Period": tx_path.parts[-3],
                        "TX Records": tx_count,
                        "TX Size (MB)": round(tx_size, 2),
                        "CT Records": ct_count,
                        "CT Size (MB)": round(ct_size, 2),
                        "Status": "Found in Lake"
                    })
        
        if not found_in_lake:
            results.append({
                "Company": search_name,
                "Matched Name": matches["legal_name"][0],
                "CID": cids[0],
                "Status": "Found in Index, not in Lake"
            })
            
    return results

if __name__ == "__main__":
    data = find_company_data()
    for d in data:
        print(d)
