import polars as pl
import os

file_path = "./tower.docs/FERC EQR SAMPLES/EQR_Validation_Rules_2.xlsx"
output_path = "./scratch/validation_rules.md"

def excel_to_markdown(file_path, output_path):
    try:
        # Get all sheet names
        # Polars read_excel doesn't have a direct way to get sheet names easily in older versions
        # but let's try with pandas first as it's more flexible for exploration
        import pandas as pd
        xl = pd.ExcelFile(file_path)
        
        with open(output_path, "w") as f:
            f.write(f"# FERC EQR Validation Rules\n\n")
            for sheet_name in xl.sheet_names:
                f.write(f"## Sheet: {sheet_name}\n\n")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                # Convert to markdown table
                f.write(df.to_markdown(index=False))
                f.write("\n\n")
        print(f"Successfully wrote markdown to {output_path}")
    except Exception as e:
        print(f"Error: {e}")

excel_to_markdown(file_path, output_path)
