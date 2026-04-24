import polars as pl
import pyarrow.parquet as pq
from pathlib import Path

def generate_section_f17_tests():
    print("Generating Section F.17: Semantic & Product Consistency Fault Tests...")
    
    output_dir = Path("data/lake/section_f17")
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. CONTRACT DATA (contract.parquet) ---
    contract_records = [
        {
            "tower_unique_id": "CLEAN", "contract_unique_id": "C1",
            "customer_company_name": "BUYER CORP", "customer_id": "C00099", "customer_duns": "123",
            "affiliate": "N", "ferc_tariff_reference": "T1", "contract_execution_date": "20230101",
            "contract_commencement_date": "20230101", "service_agreement_number": "SA1",
            "product_name": "P1", "extension_provision_description": "YES", "filing_type": "NEW"
        },
        {"tower_unique_id": "F.17.1_3_FAIL", "contract_unique_id": "C2", "customer_company_name": None, "customer_id": None, "affiliate": "N", "ferc_tariff_reference": "T1", "contract_execution_date": "20230101", "contract_commencement_date": "20230101", "service_agreement_number": "SA1", "product_name": "P1", "extension_provision_description": "YES", "filing_type": "NEW"},
        {"tower_unique_id": "F.17.7_FAIL", "contract_unique_id": "C3", "customer_company_name": "B", "customer_id": "C", "affiliate": "X", "ferc_tariff_reference": "T1", "contract_execution_date": "20230101", "contract_commencement_date": "20230101", "service_agreement_number": "SA1", "product_name": "P1", "extension_provision_description": "YES", "filing_type": "NEW"},
        {"tower_unique_id": "F.17.13_FAIL", "contract_unique_id": "C4", "customer_company_name": "B", "customer_id": "C", "affiliate": "N", "ferc_tariff_reference": "T1", "contract_execution_date": "18991231", "contract_commencement_date": "20230101", "service_agreement_number": "SA1", "product_name": "P1", "extension_provision_description": "YES", "filing_type": "NEW"},
        {"tower_unique_id": "F.17.11_20_FAIL", "contract_unique_id": "C5", "customer_company_name": "B", "customer_id": "C", "affiliate": "N", "ferc_tariff_reference": "T1", "contract_execution_date": "20230101", "contract_commencement_date": "20230101", "service_agreement_number": None, "product_name": None, "extension_provision_description": "YES", "filing_type": "NEW"},
    ]
    
    pl.DataFrame(contract_records).write_parquet(output_dir / "contract.parquet")

    # --- 2. TRANSACTIONAL DATA ---
    tx_records = [{"tower_unique_id": "TX1", "transaction_unique_id": "T1", "filing_type": "NEW"}]
    tx_df = pl.DataFrame(tx_records)
    table = tx_df.to_arrow()
    meta = {"company_id": "C00017", "company_name": "AMAZON ENERGY LLC", "year": "2024", "quarter": "1", "filing_id": "F17_TEST", "filing_type": "NEW"}
    new_meta = {k.encode(): v.encode() for k, v in meta.items()}
    table = table.replace_schema_metadata(new_meta)
    pq.write_table(table, output_dir / "transaction.parquet")

if __name__ == "__main__":
    generate_section_f17_tests()
