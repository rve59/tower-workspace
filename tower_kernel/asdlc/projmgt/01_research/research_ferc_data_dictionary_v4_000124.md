# Research: FERC EQR Data Dictionary v4.0 (Order No. 917)
**ID**: `research_ferc_data_dictionary_v4_000124`
**Status**: REFERENCE
**Revision Date**: 2026-03-20 (based on simulation date)

## Overview
This document serves as a central reference for the **Electric Quarterly Report (EQR) Data Dictionary v4.0**, issued in conjunction with Order No. 917. This version marks the transition to the **XBRL-CSV standard** and defines the definitive schema for EQR filings.


## Sources


To build a high-performance validation engine in your Python 3.14t / Docker constellation, you need a specific set of "Gold Standard" technical artifacts. These samples will allow you to test the "Taxonomy as Scaffolding" ingestion logic and verify that your LadybugDB Cypher queries match the regulatory intent.

Essential Technical Documentation & Samples
Asset Type	| Source Location	| Strategic Use for Ingestion/Testing|
|-----------|-----------|-----------|
Draft Taxonomy Packages	| (eForms Portal - Taxonomy History)[https://ecollection.ferc.gov/]	| Contains the .xsd (Schema) and .xml (Linkbases). Use these to build your LadybugDB Node and Edge tables.|
XBRL-CSV Design Spec	| (FERC Vendor Files Library)[https://www.ferc.gov/filing-forms/eforms-refresh]	| Provides the blueprint for the JSON Metadata file. Critical for your "EQR Transmuter" mapping logic.|
XULE Rulesets (.zip)	| (eForms Refresh Page)[https://www.ferc.gov/filing-forms/eforms-refresh]	| The "Source Code" of validation. You will transpile these rules into the Cypher queries you'll run against the scratch DB.|
Sample Instance Files	| (eForms Refresh (Sample Instances)[https://www.ferc.gov/filing-forms/eforms-refresh]	| Official "dummy" filings. Essential for testing your FastAPI upload-to-Parquet pipeline.|
Order 917 Files	| (Order No. 917 (issued Mar 2026))[https://www.ferc.gov/power-sales-and-markets/electric-quarterly-reports-eqr]	| The definitive list of EQR fields. Use this to validate your Pydantic models for EQR transactions.|
| | (FERC EQR 917 Final Rule DD 4.0 Docs)[https://elibrary.ferc.gov/eLibrary/#] | The Data Dictionary 4.0 files
| | 




## Core Data Sections (Tables)

### 1. Identification (Filer/Seller)
Identifies the reporting entity and authorized representatives.
- **Filer Unique Identifier**: Unique ID for the entity submitting the report.
- **Seller Company Name**: Official name per FERC tariff.
- **Seller Company ID (CID)**: The 10-digit FERC CID.
- **Contact Information**: Name, Title, Email, and Phone for the filing agent.

### 2. Contract Data
Summarizes contractual terms and conditions for power and transmission sales.
- **Contract Service Agreement ID**: Unique identifier for the agreement.
- **FERC Tariff Reference**: The document authorizing the sales.
- **Contract Execution Date**: Date the agreement was signed.
- **Commencement Date**: Date jurisdictional service began.
- **Customer Company Name**: Counterparty to the agreement.
- **Affiliate Status**: (Y/N) whether the customer is an affiliate.

### 3. Transaction Data (High-Volume Fact Table)
Granular record of sales and settlement activities.
- **Transaction Unique Identifier**: Seller-assigned unique ID.
- **Product Type**: (e.g., MBR, Cost-Based, Transmission).
- **Product Name**: (e.g., Energy, Capacity, Ancillary Services).
- **Transaction Quantity**: Numerical amount sold.
- **Price**: Settlement price.
- **Rate Units**: (e.g., $/MWh, Flat Rate).
- **Standardized Quantity/Price**: Calculated metrics forエネルギー (Energy) and キャパシティ (Capacity).
- **Trade Date**: Date the transaction was executed.

### 4. Index Reporting
Tracks transactions reported to index publishers.
- **Index Publisher Identification**: Identifier for the price index services.

---

## Technical Transformation (Polars Context)

| FERC Field Category | Expected Polars dtype | Optimization |
| :--- | :--- | :--- |
| **Identifiers** | `String` | Dictionary Encoded (RLE) |
| **Dates/Timestamps** | `Date` / `Datetime` | ISO-8601 formatting |
| **Quantities/Prices** | `Float64` | Schema-enforced to prevent overflow |
| **Flags (Y/N)** | `Boolean` | Memory efficiency |

## Strategic Notes for TOWER.KERNEL
- **XBRL-CSV Blueprint**: The Data Dictionary v4.0 is the "Source of Truth" for defining our Pydantic models in `src/tower_kernel/models.py`. 
- **Validation**: Every XULE rule in the kernel must map back to one or more Field Numbers defined in this dictionary.
- **Runtime**: Execution is optimized for **Standard Python 3.14** to leverage **Polars GPU** acceleration.
