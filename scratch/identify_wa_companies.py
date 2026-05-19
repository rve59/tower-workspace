import sys
import os
from pathlib import Path

# Add the tower_kernel source to path
WORKSPACE_ROOT = Path("/home/raynier/Development/workspaces/fullstack/vibes/TOWER_WORKSPACE")
sys.path.append(str(WORKSPACE_ROOT / "tower_kernel" / "src"))

from tower_kernel.services import WashingtonDiscoveryService

if __name__ == "__main__":
    # Use the formalized service to perform the discovery
    MASTER_NAME = "CSV_2025_Q1.zip"
    OUTPUT_FILE = "washington_energy_companies.csv"
    
    print(f"Refactored: Using WashingtonDiscoveryService to scan {MASTER_NAME}")
    df = WashingtonDiscoveryService.discover_entities(
        master_zip_name=MASTER_NAME,
        output_path=OUTPUT_FILE
    )
    
    if not df.empty:
        print(f"\nSuccessfully discovered {df.height} unique Washington entities.")
        print(f"Results persisted to: {OUTPUT_FILE}")
    else:
        print("\nNo entities found or an error occurred.")
