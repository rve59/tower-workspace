
import polars as pl
import sys
import os

# Add the workspace to sys.path to import tower_kernel
sys.path.append("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE/tower_kernel/src")

from tower_kernel.rules.eqr import METADATA_RULES, registry, lake_registry, registry_rule_registry

category_map = {
    "SCHEMA":     "Type 1: Foundational",
    "STRUCTURAL": "Type 1: Foundational",
    "MANDATORY":  "Type 2: DD Foundations", 
    "LOOKUP":     "Type 2: DD Foundations",
    "IDENTITY":   "Type 2: DD Foundations",
    "ARITHMETIC": "Type 3: XULE Logic", 
    "CONSISTENCY": "Type 3: XULE Logic", 
    "CONDITIONAL": "Type 3: XULE Logic",
    "DEDUP":       "Type 3: XULE Logic",
    "HISTORICAL": "Type 4: Cross-Quarter",
    "BOUNDS":     "Type 5: Forensic",
    "AUDIT":      "Type 5: Forensic",
    "REGISTRY":   "Type 2: DD Foundations"
}

ontology = {
    "Type 1: Foundational": [],
    "Type 2: DD Foundations": [],
    "Type 3: XULE Logic": [],
    "Type 4: Cross-Quarter": [],
    "Type 5: Forensic": []
}

# 1. Add Metadata Rules
for r in METADATA_RULES:
    cat = category_map.get(r["category"], "Type 5: Forensic")
    ontology[cat].append({"id": r["id"], "desc": r["desc"]})

# 2. Add Registry Rules
for r in registry.rules:
    cat = category_map.get(r["category"], "Type 5: Forensic")
    ontology[cat].append({"id": r["rule_id"], "desc": r["description"]})

# 3. Add Lake Rules
for r in lake_registry.rules:
    cat = category_map.get(r["category"], "Type 5: Forensic")
    ontology[cat].append({"id": r["rule_id"], "desc": r["description"]})

# 4. Add Registry Rule Registry
for r in registry_rule_registry.rules:
    cat = category_map.get(r["category"], "Type 5: Forensic")
    ontology[cat].append({"id": r["rule_id"], "desc": r["description"]})

# Generate Markdown
md = "# TOWER-C Validation Rules Ontology\n\n"
for type_name, rules in ontology.items():
    md += f"## {type_name}\n"
    # Deduplicate by ID
    seen = set()
    unique_rules = []
    for r in rules:
        if r["id"] not in seen:
            unique_rules.append(r)
            seen.add(r["id"])
    
    # Sort by ID
    unique_rules.sort(key=lambda x: x["id"])
    
    for r in unique_rules:
        md += f"- **{r['id']}**: {r['desc']}\n"
    md += "\n"

print(md)
