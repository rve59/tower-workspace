## Overview
This document defines the schema for the **TOWER.KERNEL** storage layer, optimized for high-performance retrieval and validation using **Parquet** and **Polars**. 

We have moved away from GraphDB node/relationship concepts to a **High-Performance Relational Schema** that leverages Parquet-native features like dictionary encoding and predicate pushdown.

### Proposed Parquet Optimizations
1.  **Relational Flattening**: While we maintain separate tables for normalization, we have injected critical join keys (IDs) directly into the high-volume `Transaction` table. This enables Polars to perform "Star Schema" joins on the GPU with minimal overhead.
2.  **Dictionary Encoding**: Columns with low cardinality (e.g., `product_type_name`, `units`, `timezone`) are designated for Dictionary/RLE encoding, which reduces memory footprint in VRAM and speeds up filtering.
3.  **Fixed-Precision Requirements**: Parquet `DOUBLE` is used for rates/prices, but schema enforcement will ensure `DATE` and `TIMESTAMP` fields are ISO-standardized to avoid timezone drift during ingestion.
4.  **Traceability Columns**: Added `ingestion_timestamp` and `source_filename` to core tables to support the kernel's audit-trail requirements.

## Optimized Table Definitions

### 1. Table: `Seller`
*Root dimension for entity identification.*

| Property | Type | Note |
| :--- | :--- | :--- |
| `seller_company_id_ferc` | `STRING` | **Primary Key** |
| `seller_company_name` | `STRING` | Dictionary Encoded |

### 2. Table: `Contract`
*Metadata for service agreements.*

| Property | Type | Note |
| :--- | :--- | :--- |
| `global_contract_id` | `STRING` | **Primary Key** |
| `seller_company_id_ferc` | `STRING` | **Foreign Key** -> `Seller` |
| `contract_unique_id` | `STRING` | |
| `customer_company_name` | `STRING` | |
| `year_quarter` | `STRING` | Partitioning column |
| `contract_affiliate` | `BOOLEAN` | |
| `ferc_tariff_reference` | `STRING` | |
| `contract_execution_date` | `DATE` | |
| `commencement_date_of_contract_term` | `DATE` | |
| `contract_termination_date` | `DATE` | |

### 3. Table: `Contract_Term`
*Granular terms defined within a contract.*

| Property | Type | Note |
| :--- | :--- | :--- |
| `term_id` | `STRING` | **Primary Key** |
| `global_contract_id` | `STRING` | **Foreign Key** -> `Contract` |
| `product_name` | `STRING` | Dictionary Encoded |
| `product_type_name` | `STRING` | Dictionary Encoded |
| `quantity` | `DOUBLE` | |
| `units` | `STRING` | |
| `rate` | `DOUBLE` | |
| `begin_date` | `TIMESTAMP` | |
| `end_date` | `TIMESTAMP` | |

### 4. Table: `Transaction`
*High-volume fact table. Optimized for massive scans.*

| Property | Type | Note |
| :--- | :--- | :--- |
| `transaction_unique_id` | `STRING` | Filing-scoped Unique ID |
| `term_id` | `STRING` | **Foreign Key** -> `Contract_Term` |
| `seller_transaction_id` | `STRING` | |
| `transaction_begin_date` | `TIMESTAMP` | |
| `transaction_end_date` | `TIMESTAMP` | |
| `trade_date` | `DATE` | Index/Sort column |
| `product_name` | `STRING` | Denormalized for fast filtering |
| `transaction_quantity` | `DOUBLE` | |
| `price` | `DOUBLE` | |
| `total_transaction_charge` | `DOUBLE` | |
| `ingestion_timestamp` | `TIMESTAMP` | **Audit Column** |

## Relationship Mapping (Summary)

| Relationship | Logic | Implementation |
| :--- | :--- | :--- |
| `SOLD_BY` | `Contract` -> `Seller` | `seller_company_id_ferc` in `Contract` |
| `PART_OF` | `Contract_Term` -> `Contract` | `global_contract_id` in `Contract_Term` |
| `EXECUTED_UNDER` | `Transaction` -> `Contract_Term` | `term_id` in `Transaction` |
