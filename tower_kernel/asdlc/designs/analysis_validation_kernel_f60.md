# Analysis & Design: Form 60 Validation Kernel

This document details the structural requirements for validating FERC Form 60 (Service Companies) using the TOWER Kernel.

## Analysis Metrics

- **Rule Files**: 23
- **Total Assertions**: ~140
- **Alignment Operations**: 1,640
- **Primary Dimensional Scale**: Low (Associate Companies, Deferred Debits)

## Top 5 Performance Axes (Parquet Columns)

Based on frequency in the F60 XBRL instance, the following axes should be promoted to dedicated columns to optimize Polars predicate pushdown:

1. `ferc:AccountsReceivableFromAssociateCompaniesAxis`
2. `ferc:AccountsPayableToAssociateCompaniesAxis`
3. `ferc:AnalysisOfBillingAssociateCompaniesAxis`
4. `ferc:MiscellaneousDeferredDebitsAxis`
5. `ferc:MiscellaneousCurrentAndAccruedLiabilitiesAxis`

## Python / Polars Prototype

Form 60 focuses heavily on transactions with **Associate Companies**. This prototype shows how to perform a cross-concept alignment check that is scoped to associate company relationships.

```python
import polars as pl

def validate_f60_associate_transactions(df_facts: pl.DataFrame):
    """
    Example check for Form 60: Validates associate company debt/credit logic.
    """
    # 1. Select Associate Company facts
    # We use axes_hash to ensure we are comparing data for the SAME associate company
    df_assoc = df_facts.filter(
        pl.col("dimensions").list.contains(pl.struct({"axis": "ferc:AccountsReceivableFromAssociateCompaniesAxis"}))
    )

    # 2. Pivot concepts for the same Associate Company + Period
    df_aligned = df_assoc.pivot(
        values="value",
        index=["entity_id", "axes_hash", "period_label"],
        on="concept"
    )

    # 3. Rule Logic (e.g., ensuring net balances are correct)
    # Note: Column names will depend on the specific table being validated
    if "AssociateDebt" in df_aligned.columns and "AssociateCredit" in df_aligned.columns:
        return df_aligned.with_columns(
            net_balance = pl.col("AssociateDebt") - pl.col("AssociateCredit")
        )
    return df_aligned
```

## Performance Note
Form 60 is relatively small but represents a "sparse but wide" dimensional structure. Using the `axes_hash` removes the complexity of matching variable length associate company names/IDs during the alignment phase.
