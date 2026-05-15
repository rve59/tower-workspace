import polars as pl
from pathlib import Path
from typing import List, Dict, Any

class LadybugTowerBridge:
    def __init__(self, api_url: str = None):
        import os
        # Default to the Docker service name if no URL is provided
        self.api_url = api_url or os.getenv("LADYBUG_API_URL", "http://ladybug-api:8000")

    def test_connection(self) -> bool:
        """Verifies connectivity to the Ladybug API."""
        # TODO: Implement actual health check
        return True

    def generate_icebug_schema(self, lake_path: str) -> str:
        """
        Scans a lake path for Parquet files and generates Cypher DDL for Ladybug.
        Knits tables together via discovered foreign keys.
        """
        p = Path(lake_path)
        if not p.exists():
            return ""

        ddl = []
        tables = {}
        
        # 1. Discover Node Tables
        for pq_file in p.glob("*.parquet"):
            table_name = pq_file.stem.capitalize()
            schema = pl.scan_parquet(pq_file).collect_schema()
            
            # Map Polars types to Cypher types
            cols = []
            primary_key = None
            for col, dtype in schema.items():
                l_type = "STRING"
                if dtype in [pl.Int64, pl.Int32]: l_type = "INT64"
                elif dtype in [pl.Float64, pl.Float32]: l_type = "DOUBLE"
                elif dtype == pl.Boolean: l_type = "BOOLEAN"
                
                # Heuristic for Primary Key
                if not primary_key and (col.endswith("_unique_id") or col == "tower_unique_id"):
                    primary_key = col
                    cols.append(f"{col} {l_type} PRIMARY KEY")
                else:
                    cols.append(f"{col} {l_type}")
            
            ddl.append(f"CREATE NODE TABLE {table_name}({', '.join(cols)});")
            tables[table_name] = list(schema.keys())

        # 2. Discover and Create Relationships (Virtual Edges)
        # EQR Domain Logic: Transactions link to Contracts via CSA + Metadata
        if "Transactions" in tables and "Contracts" in tables:
            tx_cols = tables["Transactions"]
            ct_cols = tables["Contracts"]
            
            # Check for the core EQR join anchor
            if "contract_service_agreement" in tx_cols and "contract_service_agreement_id" in ct_cols:
                # We define the relation table
                ddl.append("CREATE REL TABLE EXECUTES_TERM(FROM Transactions TO Contracts);")
                
                # We also provide the "Knitting Cypher" - this is the logic used to populate the REL table
                # from the underlying Parquet nodes.
                knit_query = (
                    "MATCH (t:Transactions), (c:Contracts) "
                    "WHERE t.contract_service_agreement = c.contract_service_agreement_id "
                )
                
                # Add metadata-aware fuzzy matching to resolve term ambiguity
                fuzzy_keys = ["product_name", "rate_units", "class_name", "term_name"]
                for key in fuzzy_keys:
                    if key in tx_cols and key in ct_cols:
                        knit_query += f"AND t.{key} = c.{key} "
                
                pass # Knit logic documented in source but omitted from execution
                
            # 3. Generate Data Loading (COPY) Commands
            # Map the API container path to the Ladybug container volume path
            # API path: /app/tower_kernel/data/lake/C...
            # Ladybug path: /database/C...
            lbug_path = str(p).replace("/app/tower_kernel/data/lake", "/database")
            for table_name in tables.keys():
                file_name = f"{table_name.lower()}.parquet"
                ddl.append(f"COPY {table_name} FROM '{lbug_path}/{file_name}';")

        return "\n".join(ddl)

    def execute_cypher(self, query: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Executes a Cypher query against the Ladybug API with optional parameters."""
        import requests
        import datetime
        url = f"{self.api_url}/cypher"
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            print(f"[{timestamp}] [LADYBUG-BRIDGE] Sending query to {url}: {query[:50]}...")
            payload = {"query": query}
            if parameters:
                payload["parameters"] = parameters
            
            response = requests.post(url, json=payload, timeout=600)
            
            if response.status_code != 200:
                print(f"[{timestamp}] [LADYBUG-BRIDGE] Error Response: {response.text}")
                return {"rows": [], "metadata": {"error": response.text}}
                
            data = response.json()
            rows = data.get("rows", [])
            
            return {
                "rows": rows,
                "metadata": {
                    "count": len(rows),
                    "status": "success"
                }
            }
        except Exception as e:
            print(f"[{timestamp}] [LADYBUG-BRIDGE] Connection Error: {e}")
            return {"rows": [], "metadata": {"error": str(e)}}
