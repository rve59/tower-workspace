import polars as pl
from tower_kernel.rules.eqr import validate_f_16_12_1, _normalize_schema

def test_repro_f_16_12_1():
    print("--- Test 1: Valid Data (FS1 + FA1) ---")
    data = [
        {"filer_unique_id": "FA1", "seller_company_name": "Pacific Wind Lessee, LLC", "seller_cid": "C003097", "contact_name": "Barbara  Bourque"},
        {"filer_unique_id": "FS1", "seller_company_name": "Pacific Wind Lessee, LLC", "seller_cid": "C003097", "contact_name": "Ayla  Kwon"},
    ]
    df = pl.DataFrame(data).lazy()
    normalized_df = _normalize_schema(df)
    errors = validate_f_16_12_1(normalized_df).collect()
    if errors.height == 0:
        print("PASS: Valid data passed correctly.")
    else:
        print(f"FAIL: Valid data failed with: {errors['error_message'][0]}")

    print("\n--- Test 2: Missing FA1 ---")
    data_missing = [
        {"filer_unique_id": "FS1", "seller_company_name": "Pacific Wind Lessee, LLC", "seller_cid": "C003097", "contact_name": "Ayla  Kwon"},
    ]
    df_missing = pl.DataFrame(data_missing).lazy()
    normalized_missing = _normalize_schema(df_missing)
    errors_missing = validate_f_16_12_1(normalized_missing).collect()
    if errors_missing.height > 0:
        print(f"PASS: Correctly identified missing FA1: {errors_missing['error_message'][0]}")
    else:
        print("FAIL: Rule did not catch missing FA1.")

    print("\n--- Test 3: Duplicated FA1 ---")
    data_dup = [
        {"filer_unique_id": "FA1", "seller_company_name": "Pacific Wind Lessee, LLC", "seller_cid": "C003097", "contact_name": "Barbara  Bourque"},
        {"filer_unique_id": "FA1", "seller_company_name": "Pacific Wind Lessee, LLC", "seller_cid": "C003097", "contact_name": "Duplicate Agent"},
    ]
    df_dup = pl.DataFrame(data_dup).lazy()
    normalized_dup = _normalize_schema(df_dup)
    errors_dup = validate_f_16_12_1(normalized_dup).collect()
    if errors_dup.height > 0:
        print(f"PASS: Correctly identified duplicated FA1: {errors_dup['error_message'][0]}")
    else:
        print("FAIL: Rule did not catch duplicated FA1.")

if __name__ == "__main__":
    test_repro_f_16_12_1()
