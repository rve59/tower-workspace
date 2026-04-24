# Functional Design: ERP Ingestion Worker
**ID**: `fdesign_erp_ingestion_000125`
**Status**: DRAFT
**Requirement Reference**: `tdesign_kernel_data_model_000122`

## 1. Objective
Implement a high-performance ingestion worker that transforms a 4-table ERP CSV dump into a schema-enforced, partitioned Parquet lake. This worker serves as the prototype for the "Stage 1 & 2" Polars Pipeline.

## 2. Source-to-Target Mapping

### Table 1: Sellers
| ERP Field | Target Table | Target Field | Logic |
| :--- | :--- | :--- | :--- |
| `seller_id` | `Seller` | `seller_company_id_ferc` | String cast |
| `name` | `Seller` | `seller_company_name` | String trim |
| `tax_id` | (Audit) | `source_tax_id` | Captured in metadata |

### Table 2: Contracts
| ERP Field | Target Table | Target Field | Logic |
| :--- | :--- | :--- | :--- |
| `contract_id` | `Contract` | `global_contract_id` | String cast |
| `seller_id` | `Contract` | `seller_company_id_ferc` | FK reference |
| `customer_name` | `Contract` | `customer_company_name` | String trim |
| `start_date` | `Contract` | `commencement_date` | ISO Date cast |

### Table 3: Terms
| ERP Field | Target Table | Target Field | Logic |
| :--- | :--- | :--- | :--- |
| `term_id` | `ContractTerm` | `term_id` | String cast |
| `contract_id` | `ContractTerm` | `global_contract_id` | FK reference |
| `product_code` | `ContractTerm` | `product_name` | Category normalization |
| `unit_price` | `ContractTerm` | `rate` | Float64 |

### Table 4: Transactions (Fact Table)
| ERP Field | Target Table | Target Field | Logic |
| :--- | :--- | :--- | :--- |
| `tx_id` | `Transaction` | `transaction_unique_id` | Filing-scoped ID |
| `term_id` | `Transaction` | `term_id` | FK reference |
| `tx_date` | `Transaction` | `transaction_begin_date`| Datetime cast |
| `quantity` | `Transaction` | `transaction_quantity` | Float64 |
| `total_charge`| `Transaction` | `total_transaction_charge`| Computed/Verified |

---

## 3. Ingestion Pipeline (Logic)

1.  **Strict Load**: 
    *   Load CSVs using `pl.read_csv` with a pre-defined `pl.Schema`.
    *   Reject ingestion if any column types mismatch (e.g. non-numeric quantities).
2.  **Normalization**:
    *   Inject `ingestion_timestamp` and `source_filename`.
3.  **Partitioning Strategy**:
    *   Write the `Transaction` table to disk partitioned by `term_id` (or date if appropriate).
    *   Directory: `root/data/transactions/`.

## 4. Verification Criteria
- [ ] Row counts match between CSV and Parquet.
- [ ] Joins (Transactions -> Terms) resolve without nulls.
- [ ] Schema matches `models.py`.
