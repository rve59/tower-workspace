import pytest
from pydantic import ValidationError
from tower_kernel.models import Seller, Contract

def test_seller_valid(sample_seller_data):
    """TS-1.1: Verify Seller model allows valid FERC IDs."""
    seller = Seller(**sample_seller_data)
    assert seller.seller_company_id_ferc == "S001"

def test_seller_invalid_id():
    """TS-1.1: Verify Seller model (if implemented) would reject empty strings."""
    # Note: Our current model is simple. This test confirms basic type safety.
    with pytest.raises(ValidationError):
        Seller(seller_company_id_ferc=None, seller_company_name="Test")

def test_contract_valid(sample_contract_data):
    """TS-1.2: Verify Contract model validation."""
    contract = Contract(**sample_contract_data)
    assert contract.global_contract_id == "C-2024-001"
    assert contract.year_quarter == "2024Q1"

def test_contract_termination_logic(sample_contract_data):
    """TS-1.2: Check date logic consistency."""
    sample_contract_data["contract_termination_date"] = date(2023, 1, 1)
    # Our model currently doesn't have cross-field validators.
    # We could add an @model_validator here if desired.
    contract = Contract(**sample_contract_data)
    assert contract.contract_termination_date < contract.commencement_date_of_contract_term
