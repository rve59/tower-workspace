import polars as pl
import os
import io
import json
import datetime
import unittest
from unittest.mock import patch, MagicMock
from tower_kernel.services.registry_mirror import RegistryMirrorService

class TestRegistrySync(unittest.TestCase):
    REGISTRY_PATH = "data/master/registry/cid_master.parquet"
    METADATA_PATH = "data/master/registry/cid_metadata.json"

    def setUp(self):
        # Cleanup before each test
        if os.path.exists(self.REGISTRY_PATH):
            os.remove(self.REGISTRY_PATH)
        if os.path.exists(self.METADATA_PATH):
            os.remove(self.METADATA_PATH)

    @patch('urllib.request.urlopen')
    def test_sync_official_registry_mapping(self, mock_urlopen):
        # 1. Mock FERC CSV Response
        # Official headers: CID, Organization Name, Program, etc.
        mock_csv = "CID,Organization Name,Program\n" \
                   "FERC001,Official Utility A,eCollection\n" \
                   "FERC002,Official Utility B,eCollection\n"
        
        mock_response = MagicMock()
        mock_response.read.return_value = mock_csv.encode('utf-8')
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # 2. Execute Sync
        RegistryMirrorService.sync_official_registry()

        # 3. Verify Local Parquet
        self.assertTrue(os.path.exists(self.REGISTRY_PATH))
        df = pl.read_parquet(self.REGISTRY_PATH)
        
        self.assertEqual(df.height, 2)
        self.assertIn("cid", df.columns)
        self.assertIn("legal_name", df.columns)
        self.assertEqual(df.filter(pl.col("cid") == "FERC001")["legal_name"][0], "Official Utility A")
        self.assertEqual(str(df["effective_start_date"][0]), "1900-01-01")

    @patch('tower_kernel.services.registry_mirror.RegistryMirrorService.sync_official_registry')
    def test_ensure_synced_logic(self, mock_sync):
        # Case 1: No metadata -> should sync
        RegistryMirrorService.ensure_synced()
        self.assertEqual(mock_sync.call_count, 1)

        # Case 2: Metadata with today's date -> should NOT sync
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        os.makedirs(os.path.dirname(self.METADATA_PATH), exist_ok=True)
        with open(self.METADATA_PATH, 'w') as f:
            json.dump({"last_synced_date": today}, f)
        
        RegistryMirrorService.ensure_synced()
        self.assertEqual(mock_sync.call_count, 1) # Still 1

        # Case 3: Metadata with old date -> should sync
        with open(self.METADATA_PATH, 'w') as f:
            json.dump({"last_synced_date": "2000-01-01"}, f)
            
        RegistryMirrorService.ensure_synced()
        self.assertEqual(mock_sync.call_count, 2) # Incremented

if __name__ == "__main__":
    unittest.main()
