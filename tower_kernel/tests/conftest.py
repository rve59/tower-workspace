import pytest
import polars as pl
from datetime import datetime, date

@pytest.fixture
def sample_seller_data():
    return {
        "seller_company_id_ferc": "S001",
        "seller_company_name": "Test Energy Corp"
    }

@pytest.fixture
def sample_contract_data():
    return {
        "global_contract_id": "C-2024-001",
        "seller_company_id_ferc": "S001",
        "contract_unique_id": "SA-999",
        "customer_company_name": "Power Grid Inc",
        "year_quarter": "2024Q1",
        "contract_affiliate": False,
        "contract_execution_date": date(2023, 12, 1),
        "commencement_date_of_contract_term": date(2024, 1, 1),
    }

@pytest.fixture
def mock_parquet_dataset(tmp_path):
    """Creates a small mock parquet dataset for functional tests."""
    df = pl.DataFrame({
        "transaction_unique_id": ["T1", "T2"],
        "transaction_quantity": [100.0, 200.0],
        "price": [50.0, 60.0]
    })
    path = tmp_path / "test_transactions.parquet"
    df.write_parquet(path)
    return path
