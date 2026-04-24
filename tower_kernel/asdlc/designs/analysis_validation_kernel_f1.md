# Analysis & Design: Form 1 Validation Kernel

This document details the structural requirements for validating FERC Form 1 (Electric) using the TOWER Kernel.

## Analysis Metrics

- **Rule Files**: 79
- **Total Assertions**: ~1,250
- **Alignment Operations**: 8,790
- **Primary Dimensional Scale**: High (Transmission, Generating Plant, Substations)

## Top 5 Performance Axes (Parquet Columns)

Based on frequency in the F1 XBRL instance, the following axes should be promoted to dedicated columns to optimize Polars predicate pushdown:

1. `ferc:TransmissionLineStatisticsAxis`
2. `ferc:SubstationsAxis`
3. `ferc:ConstructionWorkInProgressAxis`
4. `ferc:UtilityTypeAxis`
5. `ferc:GeneratingPlantStatisticsAxis`

## Python / Polars Prototype

The following snippet demonstrates how to implement a summation rule (F1.110.1) using the `axes_hash` for high-speed alignment.

```python
import polars as pl

def validate_f1_110_1(df_facts: pl.DataFrame):
    """
    Rule F1.110.1: UtilityPlantAndConstructionWorkInProgress = UtilityPlant + ConstructionWorkInProgress
    """
    # 1. Filter for relevant concepts
    concepts = ["UtilityPlantAndConstructionWorkInProgress", "UtilityPlant", "ConstructionWorkInProgress"]
    df = df_facts.filter(pl.col("concept").is_in(concepts))

    # 2. Pivot to align components on context (entity + axes_hash + period)
    # This replaces the complex XULE alignment {} logic.
    df_aligned = df.pivot(
        values="value",
        index=["entity_id", "axes_hash", "period_label"],
        on="concept"
    )

    # 3. Vectorized validation
    df_results = df_aligned.with_columns(
        calculated_total = pl.col("UtilityPlant").fill_null(0) + pl.col("ConstructionWorkInProgress").fill_null(0),
        is_valid = (pl.col("UtilityPlantAndConstructionWorkInProgress") - (pl.col("UtilityPlant") + pl.col("ConstructionWorkInProgress"))).abs() < 1 # Simplified tolerance
    )

    return df_results.filter(pl.col("is_valid") == False)
```

## Performance Note
For Form 1, the `pivot` (or `join`) on `axes_hash` reduces the complexity from a multi-string comparison to a single integer comparison, which is critical given the ~8,800 alignment operations.
