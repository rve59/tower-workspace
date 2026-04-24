import asyncio
import datetime
import urllib.request
import json
import os
from typing import List

HUB_LOG_URL = os.getenv("HUB_LOG_URL", "http://localhost:9042/v1/system/logs/append")

class IngestionLogger:
    """
    A thread-safe log collector for ingestion progress messages.
    Supports a 'live tail' model via an async event list.
    Primarily used by the Hub (9042) to collect and stream logs to the UI.
    """
    _queue: asyncio.Queue = asyncio.Queue()
    _loop: asyncio.AbstractEventLoop = None

    @classmethod
    def set_loop(cls, loop: asyncio.AbstractEventLoop):
        """Optionally sets the loop reference for thread-safe logging."""
        cls._loop = loop

    @classmethod
    def log(cls, message: str, level: str = "INFO"):
        """Adds a message to the ingestion log queue. Safety: handles both sync and async callers."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        record = f"[{timestamp}] {level}: {message}"
        
        # Try to find a loop if not set
        loop = cls._loop
        if not loop:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # Still no loop, just print to console as fallback
                print(f"[FALLBACK] {record}")
                return

        try:
            loop.call_soon_threadsafe(cls._queue.put_nowait, record)
        except Exception as e:
            print(f"[IngestionLogger] Error pushing to queue: {e}")

    @classmethod
    async def get_stream(cls):
        """Yields messages from the queue. Blocks until a message is available."""
        while True:
            yield await cls._queue.get()

def log_progress(message: str, level: str = "INFO"):
    """
    Unified progress logger. 
    Sends logs to the centralized Hub via HTTP POST. 
    This ensures all services (Kernel, API background tasks, etc.) report to the same stream.
    """
    payload = {
        "message": message,
        "level": level
    }
    
    try:
        req = urllib.request.Request(
            HUB_LOG_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        # Use a short timeout to prevent blocking the kernel logic if hub is busy
        with urllib.request.urlopen(req, timeout=2) as response:
            pass 
    except Exception as e:
        # Fallback to local console if Hub is unreachable
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[REMOTE-LOG-FAIL] [{timestamp}] {level}: {message} (Error: {e})")
