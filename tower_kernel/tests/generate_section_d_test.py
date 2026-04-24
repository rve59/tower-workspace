import polars as pl
import pyarrow.parquet as pq
from pathlib import Path

def generate_section_d_tests():
    """
    Generates synthetic filings to trigger every rule in Section D.
    Each rule requires a specific 'filing context' (header metadata + record types).
    """
    print("Generating Section D: Structural Integrity Fault Tests...")
    
    base_record = {
        "tower_unique_id": "CLEAN",
        "transaction_unique_id": "TX_CLEAN",
        "contract_unique_id": "C1",
        "seller_company_name": "AMAZON ENERGY LLC",
        "filing_type": "NEW",
        "source_filename": "test.xml",
        "source_row_index": 0
    }

    test_scenarios = []

    # 1. SCENARIO: Header is NEW, but record is DELETE (Triggers D.3.9.1)
    # 2. SCENARIO: Header is NEW, but record is INVALID (Triggers D.3.1.2)
    new_filing_records = [
        # Clean record
        base_record.copy(),
        # D.3.9.1 Violation
        {**base_record, "tower_unique_id": "D.3.9.1_FAIL", "filing_type": "DELETE"},
        # D.3.1.2 Violation
        {**base_record, "tower_unique_id": "D.3.1.2_FAIL", "filing_type": "GHOST"},
    ]
    test_scenarios.append(("NEW", "D_SECTION_NEW.parquet", new_filing_records))

    # 3. SCENARIO: Header is REPLACE, but record is DELETE (Triggers D.3.9.2)
    replace_filing_records = [
        base_record.copy(),
        {**base_record, "tower_unique_id": "D.3.9.2_FAIL", "filing_type": "DELETE"},
    ]
    test_scenarios.append(("REPLACE", "D_SECTION_REPLACE.parquet", replace_filing_records))

    # 4. SCENARIO: Header is DELETE, but records exist (Triggers D.3.9.3 and D.3.9.9)
    delete_filing_records = [
        {**base_record, "tower_unique_id": "D.3.9.3_FAIL", "filing_type": "NEW", "source_filename": "delete_attempt.xml"},
    ]
    test_scenarios.append(("DELETE", "D_SECTION_DELETE.parquet", delete_filing_records))

    # 5. SCENARIO: Contract NEW, but mixed types (Triggers D.3.9.6)
    contract_new_mixed = [
        {**base_record, "tower_unique_id": "D.3.9.6_P1", "contract_unique_id": "C_NEW", "filing_type": "NEW"},
        {**base_record, "tower_unique_id": "D.3.9.6_FAIL", "contract_unique_id": "C_NEW", "filing_type": "DELETE"},
    ]
    test_scenarios.append(("NEW", "D_SECTION_CONTRACT_NEW.parquet", contract_new_mixed))

    # 6. SCENARIO: Contract DELETE, but transactions exist (Triggers D.3.9.8)
    contract_delete = [
        {**base_record, "tower_unique_id": "D.3.9.8_FAIL", "contract_unique_id": "C_DEL", "filing_type": "DELETE"},
    ]
    test_scenarios.append(("NEW", "D_SECTION_CONTRACT_DELETE.parquet", contract_delete))

    # Write all scenarios
    output_dir = Path("data/lake/section_d")
    output_dir.mkdir(parents=True, exist_ok=True)

    for header_type, filename, records in test_scenarios:
        df = pl.DataFrame(records)
        output_path = output_dir / filename
        
        table = df.to_arrow()
        meta = {
            "company_id": "C00017",
            "company_name": "AMAZON ENERGY LLC",
            "year": "2024",
            "quarter": "1",
            "filing_id": filename,
            "filing_type": header_type
        }
        new_meta = {k.encode(): v.encode() for k, v in meta.items()}
        table = table.replace_schema_metadata(new_meta)
        
        pq.write_table(table, output_path)
        print(f"Created {filename} (Header: {header_type})")

if __name__ == "__main__":
    generate_section_d_tests()
