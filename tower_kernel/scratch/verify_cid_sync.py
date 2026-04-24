import os
import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Patch log_progress to print to console
def log_progress_console(message: str, level: str = "INFO"):
    print(f"[{level}] {message}")

import tower_kernel.utils.logging
tower_kernel.utils.logging.log_progress = log_progress_console

import tower_kernel.services.registry_mirror
tower_kernel.services.registry_mirror.log_progress = log_progress_console

from tower_kernel.services.registry_mirror import RegistryMirrorService

def main():
    print("Starting CID Master Sync Verification (Verbose)...")
    try:
        # Trigger the official sync
        RegistryMirrorService.sync_official_registry()
        print("Sync method execution completed.")
    except Exception as e:
        print(f"Error during sync: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
