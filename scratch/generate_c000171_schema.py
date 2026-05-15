import sys
import os
from pathlib import Path

# Add the new library to sys.path
workspace_root = Path(__file__).parent.parent
sys.path.append(str(workspace_root / "ladybug.libs" / "lib_ldbg_tower_bridge" / "src"))

from lib_ldbg_tower_bridge.bridge import LadybugTowerBridge

def main():
    bridge = LadybugTowerBridge()
    lake_path = workspace_root / "tower_kernel" / "data" / "lake" / "C000171" / "2025-Q1" / "bronze"
    
    print(f"Generating schema for: {lake_path}")
    ddl = bridge.generate_icebug_schema(str(lake_path))
    
    schema_file = lake_path / "C000171_sandbox.cypher"
    schema_file.write_text(ddl)
    print(f"Schema DDL written to: {schema_file}")
    print("\n--- SCHEMA PREVIEW ---")
    print(ddl[:500] + "...")

if __name__ == "__main__":
    main()
