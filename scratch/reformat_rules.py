
import re

def reformat():
    with open('/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/scratch/validation_rules.md', 'r') as f:
        content = f.read()

    lines = content.split('\n')
    
    output = ["# FERC EQR Validation Rules\n\n"]
    
    current_rid = None
    
    # Simple state machine to find the table rows
    for line in lines:
        if not line.startswith('|'): continue
        if 'Original Req. ID' in line: continue # Header
        if ':---' in line: continue # Separator
        
        parts = [p.strip() for p in line.split('|')]
        # Parts will be ['', RID, Desc, Q3, Q4, Q1, Q2, Error, Sev, Type, ...]
        if len(parts) < 10: continue
        
        rid = parts[1]
        desc = parts[2]
        error = parts[7]
        sev = parts[8]
        vtype = parts[9]
        
        if not rid or rid == 'nan': continue
        
        output.append(f"## Original Req. ID: {rid}\n")
        output.append(f"Requirement Description: {desc}\n")
        output.append(f"Error Message: {error}\n")
        output.append(f"Severity: {sev}\n")
        output.append(f"Type of Validation: {vtype}\n\n")

    with open('/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/scratch/validation_rules.md', 'w') as f:
        f.write("".join(output))

if __name__ == "__main__":
    reformat()
