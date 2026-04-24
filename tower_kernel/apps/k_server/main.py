from fastapi import FastAPI
import uvicorn
import urllib.request
import json
import os

app = FastAPI(title="TOWER-K Node", version="0.1.0")

# Standard API endpoint for logging
HUB_LOG_URL = os.getenv("HUB_LOG_URL", "http://localhost:9042/v1/system/logs/append")

@app.get("/status")
async def get_status():
    return {
        "service": "TOWER-K",
        "port": 9043,
        "status": "OPERATIONAL"
    }

from pydantic import BaseModel
from fastapi import BackgroundTasks
from tower_kernel.ingest.master_extractor import FERCMasterExtractor
from tower_kernel.services.discovery_indexer import MasterDiscoveryService

class ExtractPayload(BaseModel):
    year: str
    quarter: str
    cid: str

@app.post("/v1/ingest/extract")
async def extract_master(payload: ExtractPayload, background_tasks: BackgroundTasks):
    """
    Triggers the high-performance Master ZIP extraction in the Kernel process space.
    """
    from tower_kernel.utils.logging import log_progress
    
    def run_extraction():
        try:
            # Removed int() casts to keep normalization in the service layer
            extractor = FERCMasterExtractor(payload.year, payload.quarter, payload.cid)
            extractor.extract()
        except Exception as e:
            log_progress(f"CRITICAL ERROR in extraction background task: {e}", "ERROR")

    background_tasks.add_task(run_extraction)
    return {"status": "extraction_dispatched", "cid": payload.cid}

@app.post("/test-log")
async def test_log(message: str = "Hello from TOWER-K (9043)"):
    """
    Sends a test log message to the 9042 Log Hub.
    """
    payload = {
        "message": f"[TOWER-K] {message}",
        "level": "INFO"
    }
    
    try:
        req = urllib.request.Request(
            HUB_LOG_URL, 
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            return {"status": "dispatched", "hub_response": result}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.post("/v1/system/rebuild-index")
async def rebuild_discovery_index(background_tasks: BackgroundTasks):
    """
    Triggers a full scan of all Master Quarterly ZIPs to build an authoritative
    discovery registry of CID -> Technical ID mappings.
    """
    background_tasks.add_task(MasterDiscoveryService.rebuild_index)
    return {"status": "indexing_dispatched"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9043)
