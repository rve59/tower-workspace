# TOWER System Blueprint: Service Layer Registry

This document serves as the **Source of Truth** for the TOWER-C (Filer Edition) application architecture. It tracks the relationship between business functions, their implementation files, and the supporting Data Lake infrastructure.

## 1. Functional Registry (TOWER-C Services)

Detailed mapping of user-facing features to backend service implementations.

| Service | Feature | Backend Implementation | Status |
| :--- | :--- | :--- | :--- |
| **Workspace** | Load Draft CSVs | `workspace.load_draft_submission()` | [ ] Pending |
| **Workspace** | Clear Scratch Space | `workspace.clear_workspace()` | [ ] Pending |
| **Diagnostic** | Pre-Flight Scorecard | `diagnostic.get_compliance_scorecard()` | [ ] Pending |
| **Diagnostic** | Error Drill-down | `diagnostic.get_rule_evidence()` | [ ] Pending |
| **Diagnostic** | Export Audit Report | `diagnostic.export_compliance_report()` | [ ] Pending |

## 2. File Architecture

Registry of core files serving the and TOWER-C interaction layer.

| File Path | Role | Description |
| :--- | :--- | :--- |
| `src/tower_kernel/services/workspace.py` | Orchestrator | Manages the ingestion of local draft files into the lake. |
| `src/tower_kernel/services/diagnostic.py` | Orchestrator | Aggregates results from the rule registry for the UI. |
| `src/tower_kernel/rules/eqr.py` | Engine | Core logic for all 100+ EQR validation rules. |
| `src/tower_kernel/ingest/streaming.py` | Library | Utility for disk-backed streaming of large CSV/Zip data. |

## 3. Data Lake Map (Lake Tiers)

Overview of how data is structured and partitioned for high-performance scanning.

### A. The Master Representative Lake
*   **Path**: `data/lake/transactions/`
*   **Partitioning**: `year_quarter={YYYYQN}/company_id={CID}/`
*   **Role**: Persistent store for fully ingested and validated files.

### B. The Filer Workspace (Draft Tier)
*   **Path**: `data/workspace/drafts/`
*   **Partitioning**: `user_id={UID}/session_id={SID}/`
*   **Role**: Transient storage for local files currently being "fixed" before submission.

### C. The Artifact Store
*   **Path**: `data/reports/`
*   **Role**: Storage for persisted validation results (snapshots).

## 4. Workflows

### A. The "Compliance Scorecard" Workflow
1.  **Selection**: UI picks a `session_id`.
2.  **Scan**: `DiagnosticService` scans the Draft Tier using Polars `scan_parquet`.
3.  **Triage**: `run_benchmarked_validation` generates a LazyFrame of errors.
4.  **Aggregate**: Group-by `rule_id` and `category` to calculate the Scorecard.
5.  **Return**: JSON summary to TOWER-C.

### B. The "Fix List" Drill-down
1.  **Selection**: UI picks a `rule_id`.
2.  **Filter**: `DiagnosticService` filters the triage results for that ID.
3.  **Fetch**: Retrieve the first 100 records with original `source_row_index`.
4.  **Display**: Show specific transaction data alongside the remediation text.
