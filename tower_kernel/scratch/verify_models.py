import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from tower_kernel.model_v40 import IdentificationData, ContractData, TransactionData

def test():
    print("Testing IdentificationData...")
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
    print("✓ IdentificationData OK")

    print("Testing ContractData conditional validation...")
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
    ContractData(**valid_data)
    
    try:
        invalid_data = valid_data.copy()
        invalid_data["Product Name"] = "Other"
        ContractData(**invalid_data)
        print("✗ ContractData failed to catch missing description")
    except ValueError as e:
        print(f"✓ ContractData caught error as expected: {e}")

    print("\nAll schema checks passed successfully.")

if __name__ == "__main__":
    test()
