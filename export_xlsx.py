import json
from pathlib import Path
import xlsxwriter

# Define paths
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
JSON_PATH = WORKSPACE_ROOT / "scratch" / "validation_results.json"
XLSX_PATH = WORKSPACE_ROOT / "scratch" / "validation_results.xlsx"

def extract_errors(result_str):
    import re
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

    cids = list(data.keys())
    if not cids:
        return
        
    first_cid_data = data[cids[0]]
    rule_codes = [rule["code"] for rule in first_cid_data]
    rule_names = {rule["code"]: rule.get("name", "No description provided") for rule in first_cid_data}

    # Create an new Excel file and add a worksheet.
    workbook = xlsxwriter.Workbook(str(XLSX_PATH))
    worksheet = workbook.add_worksheet("Validation Results")

    # Format for headers
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#f3f3f3',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })

    # Write headers
    worksheet.write(0, 0, "CID", header_format)
    
    # Freeze the top row and first column so it's easy to scroll
    worksheet.freeze_panes(1, 1)

    for col_num, code in enumerate(rule_codes, start=1):
        worksheet.write(0, col_num, code, header_format)
        # Add the hover-note (comment) to the cell
        # We clean the string just in case there are weird characters
        note_text = str(rule_names.get(code, "No description"))
        worksheet.write_comment(0, col_num, note_text, {'author': 'TOWER Validation Engine'})

    # Write rows
    for row_num, cid in enumerate(data.keys(), start=1):
        worksheet.write(row_num, 0, cid, cell_format)
        
        rule_map = {r["code"]: r["result"] for r in data[cid]}
        
        for col_num, code in enumerate(rule_codes, start=1):
            result_str = rule_map.get(code, "N/A")
            val = extract_errors(result_str)
            
            # Write numbers as actual numbers and strings as strings
            if isinstance(val, int):
                worksheet.write_number(row_num, col_num, val, cell_format)
            else:
                worksheet.write_string(row_num, col_num, str(val), cell_format)

    workbook.close()
    print(f"Excel file with hover-notes exported to {XLSX_PATH}")

if __name__ == "__main__":
    main()
