# Analysis & Design: Form 6 Validation Kernel

This document details the structural requirements for validating FERC Form 6 (Oil) using the TOWER Kernel.

## Analysis Metrics

- **Rule Files**: 40
- **Total Assertions**: ~380
- **Alignment Operations**: 3,830
- **Primary Dimensional Scale**: Medium (Pipeline Mileage, Ownership, Products)

## Top 5 Performance Axes (Parquet Columns)

Based on frequency in the F6 XBRL instance, the following axes should be promoted to dedicated columns to optimize Polars predicate pushdown:

1. `ferc:MilesOfPipelineOperatedAxis`
2. `ferc:OwnershipAxis`
3. `ferc:StateOfOriginAndProductTypeAxis`
4. `ferc:ProductsAndServicesAxis`
5. `ferc:PipelineTaxesAxis`

## Python / Polars Prototype

Form 6 rules often aggregate data across geographic states or product types. This prototype demonstrates a "Grouped Alignment," where we validate that the sum of states equals the national total.

```python
import polars as pl

def validate_f6_geographic_sum(df_facts: pl.DataFrame):
    """
    Example check for Form 6: Validates that state-level facts sum to the total.
    """
    # 1. Select the concept and explode the dimensions to find State-level facts
    # We filter for facts that HAVE the StateOfOriginAndProductTypeAxis
    df_states = df_facts.filter(
        pl.col("concept") == "BarrelsOfOilReceived",
        pl.col("dimensions").list.contains(pl.struct({"axis": "ferc:StateOfOriginAndProductTypeAxis"}))
    )

    # 2. Aggregation by the dimension (summing all states)
    # We keep entity and period_label as the grouping keys
    df_calc = df_states.group_by(["entity_id", "period_label"]).agg(
        calculated_total = pl.col("value").sum()
    )

    # 3. Join with the Total fact (which has NO State dimension)
    # Total facts usually have a null axes_hash or a 'Global' hash.
    df_total = df_facts.filter(
        pl.col("concept") == "BarrelsOfOilReceivedTotal",
        pl.col("axes_hash") == 0  # Assuming 0 is the hash for 'No Dimensions'
    )

    df_final = df_calc.join(df_total, on=["entity_id", "period_label"])
    
    return df_final.with_columns(
        is_valid = (pl.col("calculated_total") == pl.col("value"))
    ).filter(pl.col("is_valid") == False)
```

## Performance Note
Form 6 mileage and product checks involve high-cardinality dimensions. Using Polars' `group_by` on `entity_id` combined with dimension filtering provides the most scalable approach for oil pipeline datasets.
