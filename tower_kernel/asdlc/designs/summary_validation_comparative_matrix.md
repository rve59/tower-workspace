# Comparative Matrix: FERC Form Rule Sets

This document provides a high-level comparison of the rule sets for all supported FERC forms. It serves as a sizing guide for the TOWER Kernel validation engine and highlights the primary dimensional complexities for each form.

## Sizing Matrix

| Form | Assertions (Total) | Alignment Joins (`{}`) | Rule Files | Primary Complexity Axis | Est. Ingestion Rows (Facts) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F1** | ~1,250 | **8,790** | 79 | `TransmissionLineStatisticsAxis` | ~40,000 |
| **F2** | ~680 | **8,260** | 75 | `TaxesAccruedPrepaidAndChargedAxis` | ~30,000 |
| **F6** | ~380 | 3,830 | 40 | `MilesOfPipelineOperatedAxis` | ~15,000 |
| **F60** | ~140 | 1,640 | 23 | `AccountsReceivableFromAssociateCompaniesAxis` | ~5,000 |
| **F714** | ~50 | 287 | 9 | `PlanningAreaHourlyDemandAxis` | ~4,000 |

## Performance Insights

> [!IMPORTANT]
> **Join Concentration**: Forms **F1** and **F2** account for over 80% of the total validation join volume. High-performance `axes_hash` indexing is mandatory for these forms to achieve multi-filing validation in seconds.

### Alignment Ratio
The "Alignment per Assertion" ratio indicates how many joins are typically required for a single rule:
- **F2** has the highest density (~12 alignments per rule), largely due to complex multi-utility taxes and rates logic.
- **F714** is the least complex (~5 alignments per rule), focusing on balance-of-load checks.

### Recommended Kernel Strategy
- **Dictionary Encoding**: Mandatory for `concept` and `member` columns across all forms.
- **Dedicated Columns**: In the Parquet kernel, promote the **Top 5 most frequent axes** per form to dedicated boolean or low-cardinality columns for faster predicate pushdown in Polars.
