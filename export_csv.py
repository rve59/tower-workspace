import json
import csv
import re
from pathlib import Path

# Define paths
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
JSON_PATH = WORKSPACE_ROOT / "scratch" / "validation_results.json"
CSV_PATH = WORKSPACE_ROOT / "scratch" / "validation_results.csv"

def extract_errors(result_str):
    if result_str == "Passed":
        return 0
    elif result_str.startswith("Failed (") and "violations" in result_str:
        # Extract number from "Failed (123 violations)"
        match = re.search(r"Failed \((\d+) violations\)", result_str)
        if match:
            return int(match.group(1))
    return result_str  # For execution failures or unhandled cases

def main():
    if not JSON_PATH.exists():
        print(f"File {JSON_PATH} not found.")
        return

    with open(JSON_PATH, "r") as f:
        data = json.load(f)

    if not data:
        print("No data in JSON file.")
        return

    # To ensure consistent columns, gather all unique rule codes in the order they appear
    # We assume the first CID has the full ordered list.
    cids = list(data.keys())
    if not cids:
        return
        
    first_cid_data = data[cids[0]]
    rule_codes = [rule["code"] for rule in first_cid_data]

    # Prepare CSV data
    headers = ["CID"] + rule_codes
    rows = []

    for cid, rules in data.items():
        row = {"CID": cid}
        # Build a lookup for this CID's rules
        rule_map = {r["code"]: r["result"] for r in rules}
        
        for code in rule_codes:
            result_str = rule_map.get(code, "N/A")
            row[code] = extract_errors(result_str)
            
        rows.append(row)

    # Write to CSV
    with open(CSV_PATH, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"CSV exported to {CSV_PATH}")

if __name__ == "__main__":
    main()
