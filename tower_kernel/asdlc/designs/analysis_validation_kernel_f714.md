# Analysis & Design: Form 714 Validation Kernel

This document details the structural requirements for validating FERC Form 714 (Balancing Authority) using the TOWER Kernel.

## Analysis Metrics

- **Rule Files**: 9
- **Total Assertions**: ~50
- **Alignment Operations**: 290
- **Primary Dimensional Scale**: Low/Time-Series (Hourly Demand, Monthly Peaks)

## Top 5 Performance Axes (Parquet Columns)

Based on frequency in the F714 XBRL instance, the following axes should be promoted to dedicated columns to optimize Polars predicate pushdown:

1. `ferc:MonthAxis`
2. `ferc:PlanningAreaHourlyDemandAndForecastSummerAndWinterPeakDemandAndAnnualNetEnergyForLoadAxis`
3. `ferc:AdjacentBalancingAuthorityAreaInterconnectionsAxis`
4. `ferc:BalancingAuthorityAreaScheduledAndActualInterchangeAxis`
5. `ferc:GeneratingPlantsIncludedInReportingBalancingAuthorityAreaAxis`

## Python / Polars Prototype

Form 714 is unique as it contains **Hourly Time-Series data**. This prototype demonstrates how to use the `axes_hash` (which includes the specific hour/time dimensions) to perform a daily total validation.

```python
import polars as pl

def validate_f714_hourly_total(df_facts: pl.DataFrame):
    """
    Example check for Form 714: Validates that 24 hourly values align with a daily fact.
    """
    # 1. Filter for Hourly Demand facts
    # We use a dimension filter for the hourly axis
    df_hourly = df_facts.filter(
        pl.col("concept") == "HourlyDemand",
        pl.col("dimensions").list.contains(pl.struct({"axis": "ferc:PlanningAreaHourlyDemand...Axis"}))
    )

    # 2. Extract Date from context (Ignoring the Hour component for grouping)
    # We group by entity, period, and any other axes (like Planning Area)
    df_daily_calc = df_hourly.group_by(["entity_id", "period_label"]).agg(
        day_total = pl.col("value").sum()
    )

    # 3. Compare with the reported Daily Total fact
    df_daily_fact = df_facts.filter(pl.col("concept") == "TotalDailyEnergy")

    return df_daily_calc.join(df_daily_fact, on=["entity_id", "period_label"])
```

## Performance Note
Form 714 is the smallest rule set but handles the deepest "Vertical" data (8,760 hours per year). For 714, the TOWER Kernel should leverage **Polars' time-series window functions** if any rules require rolling averages or peak-load detection across hours.
