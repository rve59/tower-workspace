import polars as pl
import sys

file_path = "./tower.docs/FERC EQR SAMPLES/EQR_Validation_Rules_2.xlsx"

try:
    print("Trying Polars with calamine (default)...")
    df = pl.read_excel(file_path)
    print("Successfully read with Polars:")
    print(df)
except Exception as e:
    print(f"Polars (default) error: {e}")
    try:
        print("Trying Polars with fastexcel...")
        df = pl.read_excel(file_path, engine="fastexcel")
        print("Successfully read with Polars (fastexcel):")
        print(df)
    except Exception as e2:
        print(f"Polars (fastexcel) error: {e2}")
        try:
            import pandas as pd
            print("Trying Pandas...")
            df = pd.read_excel(file_path)
            print("Successfully read with Pandas:")
            print(df)
        except Exception as e3:
            print(f"Pandas error: {e3}")
