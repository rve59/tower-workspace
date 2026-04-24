import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import os

def test_metadata():
    df = pl.DataFrame({"a": [1, 2, 3]})
    table = df.to_arrow()
    
    # Add metadata
    existing_metadata = table.schema.metadata or {}
    new_metadata = {
        **existing_metadata,
        b"company_id": b"12345",
        b"company_name": b"Test Corp"
    }
    table = table.replace_schema_metadata(new_metadata)
    
    pq.write_table(table, "test_meta.parquet")
    
    # Read back
    meta = pq.read_metadata("test_meta.parquet")
    print(f"Metadata: {meta.metadata}")
    os.remove("test_meta.parquet")

if __name__ == "__main__":
    test_metadata()
