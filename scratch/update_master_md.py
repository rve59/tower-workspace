import json
import re

# Read registry
with open("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/src/tower_kernel/rules/eqr_rules_registry.json") as f:
    registry = json.load(f)

# Read master md
with open("/home/raynier/.gemini/antigravity/brain/281ee22d-7801-4eb2-ad80-26be8b450ab0/artifacts/eqr_rules_master.md") as f:
    master_content = f.read()

# Parse the table rows
lines = master_content.splitlines()
table_lines = []
for line in lines:
    if line.strip().startswith('|') and not line.strip().startswith('| Rule Code'):
        # Skip headers separator
        if ':---' in line:
            continue
        table_lines.append(line)

rules = []
for tl in table_lines:
    parts = [p.strip() for p in tl.split('|')[1:-1]]
    if len(parts) >= 2:
        rule_code = parts[0]
        desc = parts[1]
        rules.append((rule_code, desc))

# Generate the new markdown
out = []
out.append("# Master Rule Tracking: EQR Validation Rules\n")
out.append("| Rule Code | Description | Feasibility | Implementation Status |")
out.append("| :--- | :--- | :--- | :--- |")

# Keep the original table (updating status if implemented)
for tl in table_lines:
    parts = [p.strip() for p in tl.split('|')[1:-1]]
    if len(parts) >= 4:
        rule_code = parts[0]
        desc = parts[1]
        feasibility = parts[2]
        status = parts[3]
        
        # If implemented in registry, mark as Active [x]
        if rule_code in registry:
            status = "[x] Active"
        
        out.append(f"| {rule_code} | {desc} | {feasibility} | {status} |")

out.append("\n---\n")
out.append("# Declarative Cypher Queries by Rule\n")

for rule_code, desc in rules:
    out.append(f"## Rule {rule_code}")
    out.append(f"**Description**: {desc}\n")
    if rule_code in registry:
        cypher = registry[rule_code]["cypher"]
        out.append("```cypher")
        out.append(cypher)
        out.append("```\n")
    else:
        out.append("*No Cypher query implemented yet (Pending).*\n")

# Write new file
with open("/home/raynier/.gemini/antigravity/brain/281ee22d-7801-4eb2-ad80-26be8b450ab0/artifacts/eqr_rules_master.md", "w") as f:
    f.write("\n".join(out) + "\n")

print("Successfully updated eqr_rules_master.md with sub-chapters and Cypher queries!")
