import pytest
from tower_kernel.model_v40 import IdentificationData, ContractData, TransactionData

def test_identification_data_valid():
    data = {
        "Seller": "Test Utility LLC",
        "Seller CID": "C123456",
        "Seller Contact": "John Doe",
        "Seller Contact Phone": "555-0199",
        "Seller Contact Email": "john.doe@test.com",
        "Filing Quarter": 1,
        "Filing Year": 2025,
        "Qualifying Facility": "Y",
        "Notes": "Initial filing"
    }
    model = IdentificationData(**data)
    assert model.seller_cid == "C123456"
    assert model.filing_quarter == 1

def test_identification_data_invalid_cid():
    data = {
        "Seller": "Test Utility LLC",
        "Seller CID": "123456", # Missing 'C'
        "Seller Contact": "John Doe",
        "Seller Contact Phone": "555-0199",
        "Seller Contact Email": "john.doe@test.com",
        "Filing Quarter": 1,
        "Filing Year": 2025,
        "Qualifying Facility": "Y"
    }
    with pytest.raises(ValueError, match="Seller CID must be a 6-digit integer preceded by 'C'"):
        IdentificationData(**data)

def test_contract_data_conditional_desc():
    valid_data = {
        "Contract Unique ID": "C-001",
        "Seller": "Test Utility LLC",
        "Customer is RTO/ISO": "N",
        "Customer Company Name": "Buyer Corp",
        "Contract Affiliate": "N",
        "FERC Tariff Reference": "Tariff 1",
        "Contract Service Agreement ID": "SA-100",
        "Contract Execution Date": "20250101",
        "Commencement Date of Contract Terms": "20250101",
        "Extension Provision Description": "None",
        "Class Name": "F",
        "Term Name": "LT",
        "Increment Name": "H - Hourly",
        "Increment Peaking Name": "FP",
        "Product Type": "MB",
        "Product Name": "ENERGY",
        "Rate Description": "Fixed rate"
    }
    # Should work
    ContractData(**valid_data)

    # Should fail if Product Name is "Other" and no description
    invalid_data = valid_data.copy()
    invalid_data["Product Name"] = "Other"
    with pytest.raises(ValueError, match="Product Name Description is required if Product Name is Other or Bundled"):
        ContractData(**invalid_data)

def test_transaction_data_valid():
    data = {
        "Seller": "Test Utility LLC",
        "Customer Company Name": "Buyer Corp",
        "Transaction Unique ID": "T-999",
        "FERC Tariff Reference": "Tariff 1",
        "Contract Service Agreement ID": "SA-100",
        "Transaction Identifier": "TX-1",
        "Transaction Begin Date": "202501010000",
        "Transaction End Date": "202501010100",
        "Trade Date": "20241220",
        "Type of Rate": "Fixed",
        "Time Zone": "ES",
        "PODBAA": "PJM",
        "Class Name": "F",
        "Term Name": "ST",
        "Increment Name": "H - Hourly",
        "Increment Peaking Name": "FP",
        "Product Name": "ENERGY",
        "Transaction Quantity": 100.0,
        "Price": 50.0,
        "Rate Units": "$/MWH",
        "Total Transmission Charge": 0.0,
        "Total Transaction Charge": 5000.0
    }
    model = TransactionData(**data)
    assert model.total_transaction_charge == 5000.0
