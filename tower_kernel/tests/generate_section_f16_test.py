import polars as pl
import pyarrow.parquet as pq
from pathlib import Path

def generate_section_f16_tests():
    """
    Generates synthetic transactional data and an identity dimension table
    to trigger Section F.16 (Identification Data) rules.
    """
    print("Generating Section F.16: Identification Data Fault Tests...")
    
    output_dir = Path("data/lake/section_f16")
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. IDENTITY DIMENSION DATA (identity.parquet) ---
    identity_records = [
        {"filer_unique_id": "FA1", "contact_name": "Compliance Agent", "contact_title": "Officer", "contact_email": "agent@amazon.com"},
        {"filer_unique_id": "FA1", "contact_name": "Duplicate Agent", "contact_title": "Officer", "contact_email": "invalid-email"},
    ]
    pl.DataFrame(identity_records).write_parquet(output_dir / "identity.parquet")

    # --- 2. CONTRACT DATA (contract.parquet) ---
    contract_records = [
        {"contract_unique_id": "C1", "seller_id": "C00017", "filing_type": "NEW"}
    ]
    pl.DataFrame(contract_records).write_parquet(output_dir / "contract.parquet")

    # --- 3. TRANSACTIONAL DATA (transaction.parquet) ---
    tx_records = [
        {
            "tower_unique_id": "CLEAN", "transaction_unique_id": "TX1",
            "seller_company_name": "AMAZON ENERGY LLC", "seller_id": "C00017", "seller_duns": "123456789",
            "contact_name": "Jane Doe", "contact_title": "Compliance", "contact_phone": "555-0199", "contact_email": "jane@amazon.com",
            "contact_address_1": "123 Amazon Way", "contact_city": "Seattle", "contact_zip_code": "98101", "filing_type": "NEW"
        },
        {"tower_unique_id": "F.16.14_FAIL", "transaction_unique_id": "TX2", "seller_company_name": None, "seller_id": None, "seller_duns": "123456789", "contact_name": "Jane", "contact_title": "C", "contact_phone": "555", "contact_email": "j@a.com", "contact_address_1": "A1", "contact_city": "C1", "contact_zip_code": "12345", "filing_type": "NEW"},
        {"tower_unique_id": "F.16.5_10_FAIL", "transaction_unique_id": "TX3", "seller_company_name": "A", "seller_id": "C", "seller_duns": "1", "contact_name": None, "contact_title": "C", "contact_phone": "555", "contact_email": "j@a.com", "contact_address_1": None, "contact_city": "C1", "contact_zip_code": "12345", "filing_type": "NEW"},
        {"tower_unique_id": "F.16.13_FAIL", "transaction_unique_id": "TX4", "seller_company_name": "A", "seller_id": "C", "seller_duns": "1", "contact_name": "J", "contact_title": "C", "contact_phone": "555", "contact_email": "j@a.com", "contact_address_1": "A1", "contact_city": None, "contact_zip_code": "BAD", "filing_type": "NEW"},
        {"tower_unique_id": "F.16.15_FAIL", "transaction_unique_id": "TX5", "seller_company_name": "A", "seller_id": "C", "seller_duns": "NAN", "contact_name": "J", "contact_title": "C", "contact_phone": "555", "contact_email": "j@a.com", "contact_address_1": "A1", "contact_city": "C1", "contact_zip_code": "12345", "filing_type": "NEW"},
        {"tower_unique_id": "F.16.6_7_FAIL", "transaction_unique_id": "TX6", "seller_company_name": "A", "seller_id": "C", "seller_duns": "1", "contact_name": "J", "contact_title": None, "contact_phone": None, "contact_email": "j@a.com", "contact_address_1": "A1", "contact_city": "C1", "contact_zip_code": "12345", "filing_type": "NEW"},
    ]
    
    tx_df = pl.DataFrame(tx_records)
    table = tx_df.to_arrow()
    meta = {"company_id": "C00017", "company_name": "AMAZON ENERGY LLC", "year": "2024", "quarter": "1", "filing_id": "F16_TEST", "filing_type": "NEW"}
    new_meta = {k.encode(): v.encode() for k, v in meta.items()}
    table = table.replace_schema_metadata(new_meta)
    pq.write_table(table, output_dir / "transaction.parquet")

if __name__ == "__main__":
    generate_section_f16_tests()
