# Technical Specification: TOWER Kernel Ingestion Format (v1)

This document defines the formal schema for the TOWER platform's ingestion format. This format serves as the shared contract between the XBRL parsers (Ingestion Workers) and the TOWER-K Validation Engine.

## 1. Governance & Storage Strategy

- **Dataset Isolation**: Every FERC form (F1, F2, F6, F60, F714) MUST be stored in a separate Parquet dataset. 
- **Partitioning**: In the "Regulator Edition," datasets should be partitioned by `report_year` and `legal_entity_id` to enable high-efficiency directory pruning.
- **Tokenization**: All high-redundancy string columns (Respondent Name, Concept, Units, etc.) MUST use **Parquet Dictionary Encoding**.

---

## 2. Schema Definition

### Administrative Metadata (Tokenized)
| Column | Type | Encoding | Description |
| :--- | :--- | :--- | :--- |
| `filing_id` | String | Dictionary | Unique identifier (e.g., Accession Number). Serves as the root for all audit trails. |
| `legal_entity_id` | String | Dictionary | The CID or LEI of the respondent. |
| `respondent_name` | String | Dictionary | The legal name of the reporting entity. |
| `report_year` | Int32 | Plain | The year being reported. |
| `report_period` | String | Dictionary | e.g., `Q4`, `Q3`. |

### Fact Data
| Column | Type | Encoding | Description |
| :--- | :--- | :--- | :--- |
| `concept` | String | Dictionary | The XBRL local concept name. |
| `value` | Float64 | Plain | The numerical value of the fact. |
| `unit` | String | Dictionary | The unit identifier (USD, Shares, etc.). |
| `decimals` | Int8 | Plain | The recorded precision of the fact. |

### Validation & Alignment Keys
| Column | Type | Encoding | Description |
| :--- | :--- | :--- | :--- |
| **`axes_hash`** | **UInt64** | **Plain** | **Stable hash of sorted dimension-member pairs. Used for O(1) context alignment.** |
| `period_label` | String | Dictionary | Pre-computed label (Current, Prior). |
| `is_instant` | Boolean | BitPacked | True for points in time; False for durations. |

### Audit Trails (Composite Pointer)
The following columns, when combined with the `filing_id`, provide a globally unique coordinate for every fact.

| Column | Type | Encoding | Description |
| :--- | :--- | :--- | :--- |
| `source_line` | Int32 | Plain | The physical line number in the source XBRL filing. |
| `source_fact_id` | String | Dictionary | The semantic `id` anchor from the source XML. |

### Dimensional Data
| Column | Type | Encoding | Description |
| :--- | :--- | :--- | :--- |
| `dimensions` | List[Struct] | Nested | Comprehensive array of `{axis, member}` pairs. |
| `[form_axis_1..5]` | String | Dictionary | **Promoted Columns** for the top 5 most frequent axes. |

---

## 3. Implementation Details

### The `axes_hash` Derivation
To ensure stability across different ingestion runs, the `axes_hash` MUST be generated as follows:
1. Extract all `xbrldi:explicitMember` and `xbrldi:typedMember` pairs.
2. Sort pairs alphabetically by Axis URI.
3. Stringify as `axis1:member1|axis2:member2|...`
4. Hash the resulting string using a stable hashing algorithm (e.g., HighwayHash or FarmHash) into a `UInt64`.

### Metadata Tokenization Rationale
Replicating `respondent_name` on every row of a 40,000-row file would typically be wasteful. By using **Dictionary Encoding**:
- The binary file stores the name string **exactly once** in a metadata dictionary.
- The 40,000 rows store only a small integer index (token) referencing that dictionary.
- This achieves the performance of a denormalized table with the storage efficiency of a normalized one.
