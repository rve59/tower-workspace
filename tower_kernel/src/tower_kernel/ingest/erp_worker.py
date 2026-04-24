import polars as pl
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ERPIngestionWorker:
    """
    Worker responsible for ingesting ERP CSV dumps into the TOWER.KERNEL Parquet lake.
    Implements Stage 1 (Strict Ingest) and Stage 2 (Columnar Normalization) of the pipeline.
    """

    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define strict schemas for ingestion
        self.schemas = {
            "sellers": {
                "seller_id": pl.String,
                "name": pl.String,
                "tax_id": pl.String,
            },
            "contracts": {
                "contract_id": pl.String,
                "seller_id": pl.String,
                "customer_name": pl.String,
                "start_date": pl.Date,
                "end_date": pl.Date,
            },
            "terms": {
                "term_id": pl.String,
                "contract_id": pl.String,
                "product_code": pl.String,
                "unit_price": pl.Float64,
                "qty_limit": pl.Float64,
            },
            "transactions": {
                "tx_id": pl.String,
                "term_id": pl.String,
                "tx_date": pl.Datetime,
                "quantity": pl.Float64,
                "total_charge": pl.Float64,
            }
        }

    def ingest_all(self):
        """Orchestrates the full ingestion process."""
        print(f"Starting ingestion from {self.source_dir}")
        
        # 1. Load and Transform Sellers
        sellers_df = self._load_csv("erp_sellers.csv", self.schemas["sellers"])
        sellers_df = sellers_df.select([
            pl.col("seller_id").alias("seller_company_id_ferc"),
            pl.col("name").alias("seller_company_name"),
        ])
        self._save_parquet(sellers_df, "sellers")

        # 2. Load and Transform Contracts
        contracts_df = self._load_csv("erp_contracts.csv", self.schemas["contracts"])
        contracts_df = contracts_df.with_columns([
            pl.col("start_date").dt.to_string("%YQ%q").alias("year_quarter"), # Rough Q extraction
            pl.lit(False).alias("contract_affiliate"), # Default for ERP mock
            pl.col("contract_id").alias("global_contract_id"),
            pl.col("seller_id").alias("seller_company_id_ferc"),
            pl.col("customer_name").alias("customer_company_name"),
            pl.col("start_date").alias("commencement_date_of_contract_term"),
            pl.col("start_date").alias("contract_execution_date"), # Simplified for mock
        ])
        self._save_parquet(contracts_df, "contracts")

        # 3. Load and Transform Terms
        terms_df = self._load_csv("erp_terms.csv", self.schemas["terms"])
        terms_df = terms_df.with_columns([
            pl.col("contract_id").alias("global_contract_id"),
            pl.col("product_code").alias("product_name"),
            pl.lit("MBR").alias("product_type_name"), # Mock default
            pl.col("unit_price").alias("rate"),
            pl.lit("MWh").alias("units"), # Mock default
            pl.datetime(2024, 1, 1).alias("begin_date"), # Simplified
            pl.datetime(2024, 12, 31).alias("end_date"),
        ])
        self._save_parquet(terms_df, "contract_terms")

        # 4. Load and Transform Transactions
        tx_df = self._load_csv("erp_transactions.csv", self.schemas["transactions"])
        tx_df = tx_df.with_columns([
            pl.col("tx_id").alias("transaction_unique_id"),
            pl.col("tx_date").alias("transaction_begin_date"),
            pl.col("tx_date").alias("transaction_end_date"),
            pl.col("tx_date").dt.date().alias("trade_date"),
            pl.col("total_charge").alias("total_transaction_charge"),
            pl.col("quantity").alias("transaction_quantity"),
            pl.lit(0).alias("price"), # To be joined or extracted
            pl.lit("Mock").alias("seller_transaction_id"),
            pl.lit("ENERGY").alias("product_name"), # Normalized
            pl.lit(datetime.now()).alias("ingestion_timestamp"),
            pl.lit("erp_transactions.csv").alias("source_filename"),
        ])
        self._save_parquet(tx_df, "transactions", partition_by=["term_id"])

        print(f"Ingestion complete. Data stored in {self.output_dir}")

    def _load_csv(self, filename: str, schema: Dict) -> pl.DataFrame:
        path = self.source_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Required source file missing: {path}")
        return pl.read_csv(path, schema=schema)

    def _save_parquet(self, df: pl.DataFrame, table_name: str, partition_by: List[str] = None):
        target_path = self.output_dir / table_name
        target_path.mkdir(parents=True, exist_ok=True)
        
        if partition_by:
            import pyarrow.dataset as ds
            # Use PyArrow to write partitioned dataset
            table = df.to_arrow()
            ds.write_dataset(
                table,
                target_path,
                format="parquet",
                partitioning=partition_by,
                existing_data_behavior="overwrite_or_ignore"
            )
        else:
            df.write_parquet(target_path / "data.parquet")

if __name__ == "__main__":
    # Internal test run
    source = Path("tower_kernel/tests/data/erp_dump")
    output = Path("tower_kernel/data/lake")
    worker = ERPIngestionWorker(source, output)
    worker.ingest_all()
