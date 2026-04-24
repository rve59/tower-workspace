import asyncio
import threading
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tower_kernel.utils.logging import IngestionLogger, log_progress
from tower_kernel.services.registry_mirror import RegistryMirrorService

async def main():
    print("Testing IngestionLogger Thread-Safety...")
    
    # Initialize the logger with the current loop
    loop = asyncio.get_running_loop()
    IngestionLogger.set_loop(loop)
    
    # Run sync in a thread
    def run_sync():
        print("Thread: Starting sync...")
        RegistryMirrorService.sync_official_registry()
        print("Thread: Sync finished.")
        
    thread = threading.Thread(target=run_sync)
    thread.start()
    
    # Listen to logs
    print("Main: Listening to logs...")
    logs_received = 0
    async for log in IngestionLogger.get_stream():
        print(f"Main: Received Log: {log}")
        logs_received += 1
        if "SUGGESTION" in log:
            print("Main: Caught suggestion log. Test PASSED.")
            break
            
    thread.join()
    print("Test Complete.")

if __name__ == "__main__":
    asyncio.run(main())
