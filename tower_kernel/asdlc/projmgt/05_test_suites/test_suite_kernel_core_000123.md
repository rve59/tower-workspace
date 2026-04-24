# Test Suite: TOWER.KERNEL Core Components
**ID**: `test_suite_kernel_core_000123`
**Status**: DRAFT
**Requirement Reference**: `tdesign_kernel_data_model_000122`

## 1. Unit Tests (Model Validation)
- [ ] **TS-1.1**: Verify `Seller` model allows valid FERC IDs and rejects empty strings.
- [ ] **TS-1.2**: Verify `Contract` model ensures `commencement_date` is ≤ `actual_termination_date`.
- [ ] **TS-1.3**: Verify `Transaction` model calculates `total_transaction_charge` correctly from `quantity * price` (if implemented in model).
- [ ] **TS-1.4**: Verify `year_quarter` regex validation (e.g., `2024Q1`).

## 2. Integration Tests (Arrow Flight Bridge)
- [ ] **TS-2.1**: Successful server-client handshake on Python 3.14t.
- [ ] **TS-2.2**: Zero-copy data handoff: Verify Arrow Record Batch integrity across the bridge.
- [ ] **TS-2.3**: Concurrent client handling: Multiple `tower.core` requests to a single `tower_kernel` instance.

## 3. Functional Snapshots (Data Integrity)
- [ ] **TS-3.1**: Row Count Verification: Compare raw CSV row count vs Parquet ingestion row count.
- [ ] **TS-3.2**: Aggregate Stability: Ensure `SUM(total_transaction_charge)` matches between source and sink.
- [ ] **TS-3.3**: Schema Drift Detection: Verify kernel rejects Parquet files with mismatched column types.

## 4. Performance Benchmarks
- [ ] **TS-4.1**: Ingestion throughput ≥ 100k rows/sec on GPU.
- [ ] **TS-4.2**: IPC Latency < 50ms for control signals.
