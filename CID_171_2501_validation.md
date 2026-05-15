# Forensic Audit Report: CID 171 (2025-Q1 Filing)

This document represents the synthetic representation of an actual FERC EQR filing for **CID 171**. This dataset is used to validate the TOWER graph engine against real-world data patterns and complex multi-contract hierarchies.

## 1. Filing Metadata
*   **Filer**: CID 171 (Market Participant)
*   **Period**: 2025-Q1
*   **Filing Type**: New
*   **Total Transactions**: 1,240
*   **Total Contracts**: 12

## 2. Sample Data Subgraph (Logical Representation)

### ID Data (Filer Identity)
| Field 1 (UID) | Field 2 (Company) | Field 13 (Index) |
| :--- | :--- | :--- |
| FS_171 | Energy Corp 171 | Y |
| FA_171 | Agency 171 | N |

### Contract Metadata (Sample Contract: C_999)
*   **Contract ID**: C_999
*   **Customer**: Regional Utility B
*   **Tariff Ref**: FERC Tariff Vol 1
*   **Commencement**: 2020-01-01
*   **Product**: Energy (Firm)

### Transaction Data (Sample Row: TX_5555)
*   **Transaction ID**: TX_5555
*   **Start Date**: 2025-01-15
*   **End Date**: 2025-01-15
*   **Product**: Energy
*   **Quantity**: 500 MWh
*   **Price**: $45.00
*   **Total Charge**: $22,500.00 (Correct)

---

## 3. Targeted Forensic Scenarios

To prove the accuracy of the TOWER engine, we have introduced **three intentional forensic anomalies** in this sample data:

1.  **F.17.1.2 Violation**: Contract `C_888` (Energy) is incorrectly labeled with Rate Units `$/MW` (Capacity units).
2.  **F.25.18 Violation**: Transaction `TX_6666` reports a product of `Ancillary Services`, but its parent contract `C_999` only authorizes `Energy`.
3.  **F.16.27.1 Violation**: The Seller `FS_171` has `ReportToIndex` set to `Y`, but the required `IndexReporting` relationship is missing.

## 4. How to Execute this Validation

To run the TOWER validation suite against this actual filing data, follow these steps:

### Step A: Data Ingestion
Load the CID 171 subgraph into the Ladybug environment using the `scratch/load_cid_171.cypher` script.

### Step B: Validation Execution
Run the validation engine (or the `test_eqr_validations.py` harness pointing to this specific CID/Period).

```bash
# In the TOWER environment:
uv run python -m tower_kernel.audit --cid 171 --period 2025Q1
```

### Step C: Forensic Reporting
Fetch the resulting violations to confirm the engine caught all three intentional anomalies.

```cypher
MATCH (v:Violation {CID: '171', FilingPeriod: '2025Q1'})
RETURN v.RuleID, v.Message, v.Severity
```
