# Analysis & Design: Form 2 Validation Kernel

This document details the structural requirements for validating FERC Form 2 (Gas) using the TOWER Kernel.

## Analysis Metrics

- **Rule Files**: 75
- **Total Assertions**: ~680
- **Alignment Operations**: 8,260
- **Primary Dimensional Scale**: High (Taxes, Rates, Subsidiary Companies)

## Top 5 Performance Axes (Parquet Columns)

Based on frequency in the F2 XBRL instance, the following axes should be promoted to dedicated columns to optimize Polars predicate pushdown:

1. `ferc:UtilityTypeAxis`
2. `ferc:TaxesAccruedPrepaidAndChargedAxis`
3. `ferc:AppliedRateTypeAxis`
4. `ferc:MonthlyQuantityAndRevenueByRateScheduleAxis`
5. `ferc:SubsidiaryCompanyAxis`

## Python / Polars Prototype

Form 2 often involves checking balances across multiple utility types. This prototype shows how to filter by a specific axis (`UtilityTypeAxis`) before performing the alignment join.

```python
import polars as pl

def validate_f2_rate_schedule(df_facts: pl.DataFrame):
    """
    Example check for Form 2: Aligns facts filtered by a specific dimension member.
    """
    # 1. Filter for facts that HAVE a specific axis member (e.g. Gas Utility)
    # This leverages the structured List[Struct] column for deep filtering.
    df_gas = df_facts.filter(
        pl.col("dimensions").list.contains(
            pl.struct({"axis": "ferc:UtilityTypeAxis", "member": "ferc:GasUtilityMember"})
        )
    )

    # 2. Perform Alignment Join on axes_hash
    # We join Current vs Prior for a simple YoY check
    df_current = df_gas.filter(pl.col("period_label") == "Current")
    df_prior = df_gas.filter(pl.col("period_label") == "Prior")

    df_yoy = df_current.join(
        df_prior,
        on=["entity_id", "axes_hash", "concept"],
        suffix="_prior"
    )

    # 3. Validation Logic
    df_results = df_yoy.with_columns(
        variance = pl.col("value") - pl.col("value_prior")
    )
    
    return df_results
```

## Performance Note
Form 2 has a high "Alignment Density" (~12 joins per rule). This makes the `axes_hash` even more critical than in Form 1, as almost every calculation is a multi-variant alignment across utility types.
