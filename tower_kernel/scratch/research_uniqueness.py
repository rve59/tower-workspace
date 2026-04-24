import zipfile
import io
import polars as pl
import os

master_path = 'tower_kernel/data/historic/CSV_2025_Q1.zip'
inner_name = 'CSV_2025_Q1_6076115_1649014.ZIP' # Puget Sound Energy

if os.path.exists(master_path):
    with zipfile.ZipFile(master_path, 'r') as m:
        with m.open(inner_name) as f:
            inner_zip_bytes = io.BytesIO(f.read())
            with zipfile.ZipFile(inner_zip_bytes, 'r') as z:
                tx_files = [n for n in z.namelist() if 'transaction' in n.lower()]
                if tx_files:
                    tx_file = tx_files[0]
                    with z.open(tx_file) as cf:
                        df = pl.read_csv(cf.read(), ignore_errors=True)
                        total = len(df)
                        unique_id = df["transaction_unique_id"].n_unique()
                        
                        print(f"Total Rows: {total}")
                        print(f"Unique Transaction Unique IDs: {unique_id}")
                        print(f"Collision Count: {total - unique_id}")
                        
                        if total != unique_id:
                            print("\nExample collisions (first 5 IDs):")
                            counts = df["transaction_unique_id"].value_counts()
                            dupes = counts.filter(pl.col("count") > 1).head(5)
                            print(dupes)
                            
                            # Test compound uniqueness
                            # Try CID + Contract ID + Product + TxID
                            df = df.with_columns(pl.lit("C000171").alias("cid"))
                            # (Normalizing names for the test)
                            compound = df.select([
                                pl.concat_str([
                                    pl.col("cid"),
                                    pl.col("contract_service_agreement"),
                                    pl.col("product_name"),
                                    pl.col("transaction_unique_id")
                                ], separator="|").alias("compound_key")
                            ])
                            
                            print(f"\nUnique Compound Keys (CID|CSA|Product|TxID): {compound['compound_key'].n_unique()}")
                else:
                    print("No transactions file found.")
else:
    print("Master zip not found")
