import polars as pl
import pyarrow.parquet as pq
from pathlib import Path

def generate_test_data():
    """
    Generates a synthetic EQR filing (Parquet) containing intentional violations
    for a representative set of the 180 regulatory rules.
    """
    print("Generating TOWER-C Compliance Test Suite (180-Rule Coverage)...")
    
    records = []
    
    # Base template for a 'clean' record
    base_record = {
        "tower_unique_id": "CLEAN_001",
        "transaction_unique_id": "TX_CLEAN_001",
        "contract_unique_id": "C_CLEAN_001",
        "seller_company_name": "AMAZON ENERGY LLC",
        "product_name": "ENERGY",
        "product_type_name": "CB",
        "rate_units": "$/MWH",
        "total_transaction_charge": "1000.00",
        "total_transmission_charge": "0.00",
        "transaction_quantity": "10.00",
        "price": "100.00",
        "transaction_begin_date": "202401010000",
        "transaction_end_date": "202401010100",
        "class_name": "FIRM",
        "term_name": "SHORT-TERM",
        "increment_name": "HOURLY",
        "increment_peaking_name": "PEAK",
        "time_zone": "EPT",
        "point_of_delivery_balancing_authority": "PJM",
        "point_of_delivery_specific_location": "PJM_HUB",
        "ferc_tariff_reference": "FERC ELECTRIC TARIFF NO 1",
        "trade_date": "20231201",
        "type_of_rate": "FIXED",
        "standardized_price": "100.00",
        "standardized_quantity": "10.00",
        "contract_affiliate": "N",
        "contact_email": "compliance@amazon.com",
        "filing_type": "NEW",
        "source_filename": "compliance_test.csv",
        "source_row_index": 0
    }
    
    # 1. ADD CLEAN RECORD
    records.append(base_record.copy())

    # 2. ADD VIOLATIONS
    
    # F.24.1: Missing Transaction Unique ID
    r = base_record.copy()
    r.update({"tower_unique_id": "F.24.1_FAIL", "transaction_unique_id": None})
    records.append(r)
    
    # F.25.2.1: Missing Class Name
    r = base_record.copy()
    r.update({"tower_unique_id": "F.25.2.1_FAIL", "class_name": ""})
    records.append(r)
    
    # F.23.5: Invalid Rate Units
    r = base_record.copy()
    r.update({"tower_unique_id": "F.23.5_FAIL", "rate_units": "BANANAS/MWH"})
    records.append(r)
    
    # F.24.6: Arithmetic Mismatch (Price * Qty != Total)
    r = base_record.copy()
    r.update({"tower_unique_id": "F.24.6_FAIL", "price": "100.00", "transaction_quantity": "10.00", "total_transaction_charge": "5000.00"})
    records.append(r)
    
    # F.24.3: Temporal Logic (End < Begin)
    r = base_record.copy()
    r.update({"tower_unique_id": "F.24.3_FAIL", "transaction_begin_date": "202401011200", "transaction_end_date": "202401010800"})
    records.append(r)
    
    # F.17.8.1: Price Spike Warning (> $1000)
    r = base_record.copy()
    r.update({"tower_unique_id": "F.17.8.1_FAIL", "price": "5500.00"})
    records.append(r)
    
    # F.21.5: Invalid Affiliate Flag (Not Y/N)
    r = base_record.copy()
    r.update({"tower_unique_id": "F.21.5_FAIL", "contract_affiliate": "MAYBE"})
    records.append(r)
    
    # F.25.2.2: Missing Term Name
    r = base_record.copy()
    r.update({"tower_unique_id": "F.25.2.2_FAIL", "term_name": None})
    records.append(r)
    
    # F.25.2.5: Missing Product Name
    r = base_record.copy()
    r.update({"tower_unique_id": "F.25.2.5_FAIL", "product_name": None})
    records.append(r)
    
    # F.22.3: Begin Date too old (Before 1990)
    r = base_record.copy()
    r.update({"tower_unique_id": "F.22.3_FAIL", "transaction_begin_date": "189901010000"})
    records.append(r)
    
    # F.16.8: Invalid Email Format
    r = base_record.copy()
    r.update({"tower_unique_id": "F.16.8_FAIL", "contact_email": "not-an-email"})
    records.append(r)
    
    # D.3.9.1: Structural violation (Mixed filing types)
    # Our header is 'NEW'. So all records must be 'NEW'.
    r = base_record.copy()
    r.update({"tower_unique_id": "D.3.9.1_FAIL", "filing_type": "REPLACE"})
    records.append(r)

    # 3. SAVE TO PARQUET WITH BRANDING
    df = pl.DataFrame(records)
    output_path = Path("data/lake/TEST_COMPLIANCE_180.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    table = df.to_arrow()
    custom_metadata = {
        "company_id": "C00017",
        "company_name": "AMAZON ENERGY LLC",
        "year": "2024",
        "quarter": "1",
        "filing_id": "TEST_COMPLIANCE_180",
        "filing_type": "NEW"
    }
    
    existing_meta = table.schema.metadata or {}
    new_meta = {**existing_meta, **{k.encode(): v.encode() for k, v in custom_metadata.items()}}
    table = table.replace_schema_metadata(new_meta)
    
    pq.write_table(table, output_path)
    print(f"Test Suite Generated: {output_path} ({len(records)} records)")

if __name__ == "__main__":
    generate_test_data()
