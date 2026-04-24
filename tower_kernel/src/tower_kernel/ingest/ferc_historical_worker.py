import polars as pl
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import uuid

class FERCHistoricalIngestionWorker:
    """
    Worker responsible for ingesting historical FERC EQR CSV files into the TOWER.KERNEL Parquet lake.
    Normalizes v3.0 era CSV schemas into the v1.0.0 TOWER models.
    """

    def __init__(self, source_dir: Path, output_dir: Path):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Historical Schema Definitions (v3.0 era)
        self.historical_schemas = {
            "ident": {
                "filer_unique_id": pl.String,
                "company_name": pl.String,
                "company_identifier": pl.String,
                "contact_name": pl.String,
                "contact_email": pl.String,
                "filing_quarter": pl.String,
            },
            "transactions": {
                "transaction_unique_id": pl.String,
                "seller_company_name": pl.String,
                "customer_company_name": pl.String,
                "ferc_tariff_reference": pl.String,
                "contract_service_agreement": pl.String,
                "transaction_unique_identifier": pl.String,
                "transaction_begin_date": pl.String, # Usually YYYYMMDDHHMM
                "transaction_end_date": pl.String,
                "trade_date": pl.String, # YYYYMMDD
                "product_name": pl.String,
                "transaction_quantity": pl.Float64,
                "price": pl.Float64,
                "rate_units": pl.String,
                "total_transaction_charge": pl.Float64,
            },
            "contracts": {
                "contract_unique_id": pl.String,
                "seller_company_name": pl.String,
                "customer_company_name": pl.String,
                "contract_affiliate": pl.String,
                "ferc_tariff_reference": pl.String,
                "contract_service_agreement_id": pl.String,
                "contract_execution_date": pl.String, # YYYYMMDD
                "commencement_date_of_contract_term": pl.String,
                "contract_termination_date": pl.String,
                "product_type_name": pl.String,
                "product_name": pl.String,
                "quantity": pl.Float64,
                "units": pl.String,
                "rate": pl.Float64,
                "rate_units": pl.String,
            }
        }

    def ingest_all(self):
        """Orchestrates the historical ingestion process."""
        print(f"Starting historical ingestion from {self.source_dir}")
        
        # 1. Load and Transform Sellers (from ident)
        ident_df = self._load_csv("sample_ident.csv", self.historical_schemas["ident"])
        sellers_df = ident_df.select([
            pl.col("company_identifier").alias("seller_company_id_ferc"),
            pl.col("company_name").alias("seller_company_name"),
        ]).unique()
        self._save_parquet(sellers_df, "sellers")

        # 2. Load and Transform Contracts & Terms
        # Historical 'contracts' CSV actually contains terms (one row per product).
        contracts_raw_df = self._load_csv("sample_contracts.csv", self.historical_schemas["contracts"])
        
        # Map Contracts
        contracts_df = contracts_raw_df.select([
            pl.col("contract_service_agreement_id").alias("global_contract_id"),
            pl.col("seller_company_name").alias("seller_company_id_ferc"), # Use name as ID if CID missing, but here we keep it consistent
            pl.col("contract_unique_id"),
            pl.col("customer_company_name"),
            pl.lit("2013Q3").alias("year_quarter"), # Hardcoded for sample or extracted from execution date
            (pl.col("contract_affiliate") == "Y").alias("contract_affiliate"),
            pl.col("ferc_tariff_reference"),
            pl.col("contract_execution_date").str.strptime(pl.Date, format="%Y%m%d", strict=False),
            pl.col("commencement_date_of_contract_term").str.strptime(pl.Date, format="%Y%m%d", strict=False),
            pl.col("contract_termination_date").str.strptime(pl.Date, format="%Y%m%d", strict=False),
        ]).unique()
        self._save_parquet(contracts_df, "contracts")

        # Map Terms
        terms_df = contracts_raw_df.with_columns([
            pl.struct(["contract_service_agreement_id", "product_name", "rate_units", "rate"])
              .map_elements(lambda x: str(uuid.uuid5(uuid.NAMESPACE_DNS, str(x))), return_dtype=pl.String)
              .alias("term_id"),
        ]).select([
            pl.col("term_id"),
            pl.col("contract_service_agreement_id").alias("global_contract_id"),
            pl.col("product_name"),
            pl.col("product_type_name"),
            pl.col("quantity"),
            pl.col("units"),
            pl.col("rate"),
            pl.datetime(2000, 1, 1).alias("begin_date"),
            pl.datetime(2099, 12, 31).alias("end_date"),
        ])
        self._save_parquet(terms_df, "contract_terms")

        # 3. Load and Transform Transactions
        tx_raw_df = self._load_csv("sample_transactions.csv", self.historical_schemas["transactions"])
        
        # Process Dates and Join with Terms
        tx_df = tx_raw_df.with_columns([
            pl.col("transaction_begin_date").str.strptime(pl.Datetime, format="%Y%m%d%H%M", strict=False),
            pl.col("transaction_end_date").str.strptime(pl.Datetime, format="%Y%m%d%H%M", strict=False),
            pl.col("trade_date").str.strptime(pl.Date, format="%Y%m%d", strict=False),
        ])

        # Link transactions to terms based on contract + product + units + price
        tx_final_df = tx_df.join(
            terms_df.select(["global_contract_id", "product_name", "units", "rate", "term_id"]),
            left_on=["contract_service_agreement", "product_name", "rate_units", "price"],
            right_on=["global_contract_id", "product_name", "units", "rate"],
            how="left"
        ).select([
            pl.col("transaction_unique_id"),
            pl.col("term_id"),
            pl.col("transaction_unique_identifier").alias("seller_transaction_id"),
            pl.col("transaction_begin_date"),
            pl.col("transaction_end_date"),
            pl.col("trade_date"),
            pl.col("product_name"),
            pl.col("transaction_quantity"),
            pl.col("price"),
            pl.col("total_transaction_charge"),
            pl.lit(datetime.now()).alias("ingestion_timestamp"),
            pl.lit("sample_transactions.csv").alias("source_filename"),
        ])

        self._save_parquet(tx_final_df, "transactions", partition_by=["term_id"])

        print(f"Historical Ingestion complete. Data stored in {self.output_dir}")

    def _load_csv(self, filename: str, schema: Dict) -> pl.DataFrame:
        path = self.source_dir / filename
        if not path.exists():
            # Try without 'sample_' prefix if not found
            alt_path = self.source_dir / filename.replace("sample_", "")
            if alt_path.exists():
                path = alt_path
            else:
                raise FileNotFoundError(f"Required source file missing: {path}")
        
        # Historical CSVs often have inconsistent quoting or encoding
        return pl.read_csv(path, schema_overrides=schema, ignore_errors=True)

    def _save_parquet(self, df: pl.DataFrame, table_name: str, partition_by: List[str] = None):
        target_path = self.output_dir / table_name
        target_path.mkdir(parents=True, exist_ok=True)
        
        if partition_by:
            import pyarrow.dataset as ds
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
    # Test stub
    import sys
    source = Path("tower.docs/FERC EQR SAMPLES/compressed-folder")
    output = Path("tower_kernel/data/lake")
    worker = FERCHistoricalIngestionWorker(source, output)
    worker.ingest_all()
