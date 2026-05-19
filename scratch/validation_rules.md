# FERC EQR Validation Rules

## Introduction: The 'Filing' Object in TOWER
In the TOWER graph architecture, a **Filing** is a synthetic semantic object that represents a single regulatory submission to FERC. While the raw EQR dataset consists of relational tables (Identity, Contract, Transaction), it does not contain a literal "Filing" table.

### Where does Filing data come from?
1. **Metadata Extraction**: The `Filing` node is synthesized during ingestion from the **ID Data (Identity)** records. The `FilingType` (e.g., New, Replace, Delete) is typically captured from the high-level attributes of the identity submission.
2. **Logical Grouping**: It serves as the root anchor for a specific **CID (Company Identifier)** within a **Filing Period (Year/Quarter)**.
3. **Forensic Scoping**: In Cypher queries, the `Filing` node allows us to scope validation rules to a specific submission (e.g., `MATCH (f:Filing {CID: 'C000171', FilingYear: 2023})`) and traverse down to its constituent contracts and transactions.

### Anatomy of a Forensic Validation Query
To understand how these rules are implemented, consider the following example pattern used throughout this document:

```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item)
WHERE item.invalid_condition 
MERGE (v:Violation {RuleID: 'D.3.9', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule D.3.9 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

*   **`(f:Filing)`**: This is the anchor. It limits the search space to a specific regulatory submission rather than the entire data lake.
*   **`-[:...*1..3]->(item)`**: This is a variable-length traversal. It efficiently scans "downstream" from the Filing root to find any problematic record (`item`), whether it is a top-level Identity record or a nested Transaction.
*   **`ON CREATE SET v.Message = ...`**: This is **Conditional Attribution**. It ensures that the specific error message and severity are only set when the `Violation` node is first created. If multiple records fail the same rule, they all link back to this single "Rule Violation" object without redundant property writes.
*   **`MERGE (item)-[:HAS_VIOLATION]->(v)`**: This is the **Forensic Link**. It creates a physical relationship between the data record that failed (`item`) and the violation record (`v`). In the TOWER interface, this is what allows a user to click on an error message and instantly see the exact Parquet row that caused it.

This graph-based abstraction allows the TOWER platform to perform cross-pillar forensic audits that are difficult to express in traditional relational SQL.

## Original Req. ID: D.3.9
Requirement Description: Refer to the “Filing Types” Tab For requirements of the manipulation of the Filing Types.
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'D.3.9', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule D.3.9 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.1
Requirement Description: For a filing with Filing.FilingType=New, all Contracts, Transactions and ContractProducts must also have FilingType=New.
Error Message: Filing rejected due to filing type inconsistency. For a filing with FilingType=New, all Contracts Data rows, Transactions Data rows and ContractProducts must also have FilingType=New. For more information on filing types or ContractProducts, please see the User’s Guide.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is New but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.2
Requirement Description: For a filing with Filing.FilingType=Replace, all Contracts, Transactions and ContractProducts must have FilingType=New.
Error Message: Filing rejected due to filing type inconsistency. For a filing with FilingType=Replace, all Contracts Data, Transactions Data and ContractProducts must have FilingType=New. For more information on filing types or ContractProducts, please see the User’s Guide.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'Replace'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is Replace but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.3
Requirement Description: For a filing with Filing.FilingType=Delete, Contracts, Transactions and ContractProducts are not allowed.
Error Message: Filing rejected due to filing type inconsistency. For a filing with FilingType=Delete, Contracts Data, Transactions Data and ContractProducts are not allowed. For more information on filing types or ContractProducts, please see the User’s Guide.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'Delete'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is Delete but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.4
Requirement Description: For a filing with Filing.FilingType=Merge, Contracts can be of any type.
Error Message: nan
Severity: No Check
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is New but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.5
Requirement Description: For a Contract Data file with Contract.FilingType=NoAction, the Transactions Data and Contract Products can have any type.
Error Message: nan
Severity: No Check
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is New but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.6
Requirement Description: For a Contract Data file with Contract.FilingType=New, all Transactions Data and ContractProducts must also have FilingType=New.
Error Message: Filing rejected due to filing type inconsistency. For a Contract Data file with FilingType=New all Transactions Data and ContractProducts must also have FilingType=New. For more information on filing types or ContractProducts, please see the User’s Guide.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is New but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.7
Requirement Description: For a Contract with Contract.FilingType=Replace, the Transactions and ContractProducts can have any type.
Error Message: nan
Severity: No Check
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'Replace'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is Replace but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.8
Requirement Description: For a Contract with Contract.FilingType=Delete, Transactions and ContractProducts are not allowed.
Error Message: Filing rejected due to a filing type inconsistency. For a Contract Data file with FilingType=Delete, Transactions Data and ContractProducts are not allowed. For more information on filing types or ContractProducts, please see the User’s Guide.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'Delete'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.8', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is Delete but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.9
Requirement Description: Disallow XML delete option for external users
Error Message: At the Filing level, XML delete is used for internal purposes only and cannot be used with external requests. However, Contract, ContractProduct and Transaction level deletes are allowed for external users.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.9', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is New but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: D.3.9.12
Requirement Description: The order of organizations in XML must be sequential
Error Message: The organizations should be listed sequentially as 1,2,3,4,5,6,…
Severity: Warning
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.12', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header (IDData) is New but component ' + labels(item)[0] + ' is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.1
Requirement Description: The validations which result in a type: “Error” will result in a rejected Submission.
Error Message: Filing rejected.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.3
Requirement Description: A filing must have at least two rows of contact data in the ID Data. A filing that is submitted without at least two ID Data (Fields 1-14) rows populated - one with Filer Unique Identifier for a Seller (indicated by FS# in Field 1) and another with Filer Unique Identifier for agent (indicated by FA# in Field 1) - shall be rejected
Error Message: A valid filing must have at least two rows of contact data in the ID Data: one with Filer Unique Identifier for a Seller (indicated by FS# in Field 1) and another with Filer Unique Identifier for agent (indicated by FA#1 in Field 1)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:IDData)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.3.1
Requirement Description: The Company Name (Field 2) shall be checked against the FERC Company Registration system.
Error Message: The Company Name (Field 2) must match the corresponding name for the same CID in Company Registration.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.3.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.3.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.3.2
Requirement Description: The Seller Company Name (Field 16) shall be checked against the FERC Company Registration system.
Error Message: The Seller Company Name (Field 16) must match the corresponding name for the same CID in Company Registration.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.3.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.3.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.3.4
Requirement Description: The Organization Company Name (Field 2) for the seller contact row (i.e., FS# in Field 1) shall be checked against the name that was effective for the same CID in Company Registration at the end of the associated Filing Period.
Error Message: The Company Name (Field 2) for the seller contact row (i.e., FS# in Field 1) must match the corresponding name that was effective for the same CID in Company Registration at the end of the associated Filing Period.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.3.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.3.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.3.5
Requirement Description: The Seller Company Name (Field 16) shall be checked against the FERC Company Registration system history. The Contract Seller Company Name (Field 16) must be a name that that was effective for the same CID in Company Registration for all or part of the associated Filing Quarter.
Error Message: The Seller Company Name (Field 16) must match a name that was effective for the same CID in Company Registration for all or part of the associated Filing Quarter.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.3.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.3.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.4.1
Requirement Description: The system shall check for the existence of duplicate ID Data (Fields 1-14).
Error Message: No Filer record found while checking for duplicates.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:IDData)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.4.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.4.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.4.2
Requirement Description: The system shall check for the existence of duplicate Filer Unique Identifiers (Field 1).
Error Message: Duplicate Filer records found using the same filer unique identifier in field 1.
Severity: Error
Type of Validation: Data Check

WITH f, node.Field_1_FilerUniqueID AS uid, collect(node) AS nodes
UNWIND nodes AS n

WITH f, node.Field_1_FilerUniqueID AS uid, collect(node) AS nodes
UNWIND nodes AS n

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(node:IDData)
WITH f, node.Field_1_FilerUniqueID AS uid, collect(node) AS nodes
WHERE size(nodes) > 1
UNWIND nodes AS n
MERGE (v:Violation {RuleID: 'F.16.4.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Duplicate ID: ' + uid, v.Severity = 'Error'
MERGE (n)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.5
Requirement Description: The system shall check for the existence of duplicate Sellers.
Error Message: Duplicate Seller records found grouped by Filer Unique Identifier for a Seller.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.6
Requirement Description: The system shall check for the existence of duplicate Sellers.
Error Message: Duplicate Seller records found. A valid filing should not include duplicate rows of ID Data. Please check that each contact has a Filer Unique Identifier for a Seller (indicated by FS# in Field 1).
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:IDData)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.7
Requirement Description: The system shall not check for duplicate contacts. There is no certain way of verifying duplicate contacts; contacts are not eRegistered and two people can have the same name and work at the same employer.
Error Message: nan
Severity: No Check
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.7 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.8
Requirement Description: The system shall check the validity of all email addresses with email Regex.
Error Message: Invalid email address found in the contact record {0}.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)-[:HAS_CONTACT]->(c:Contact)
WHERE NOT c.Field_6_Email =~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
MERGE (v:Violation {RuleID: 'F.16.8', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Invalid email format: ' + c.Field_6_Email, v.Severity = 'Error'
MERGE (c)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.10
Requirement Description: A filing shall contain zero or more Contracts.
Error Message: nan
Severity: No Check
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.10', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.10 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.11
Requirement Description: A Contract shall contain required contract data (Fields 15-44): otherwise, the system will not validate the filing if required fields are not included in the filing.
Error Message: A Contract Data row must contain all required Contract Data Fields (Fields 15 through 44).
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT]->(c:Contract)-[:HAS_TERMS]->(ct:ContractTerms)
WHERE ct.Field_15_ContractUniqueID IS NULL OR ct.Field_16_SellerCompanyName IS NULL OR ct.Field_17_CustomerCompanyName IS NULL OR ct.Field_30_ProductName IS NULL
MERGE (v:Violation {RuleID: 'F.16.11', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Contract Data Incomplete (Fields 15-44)', v.Severity = 'Error'
MERGE (ct)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.12.1
Requirement Description: A filing shall contain only one ID Data contact record with Filer Unique ID FA1.
Error Message: The ID Data does not contain a contact with a Filer Unique ID (Field 1) as indicated by FA1.
Severity: Warning
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:IDData)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.12.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.12.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.12.2
Requirement Description: A filing shall contain only one ID Data contact record with Filer Unique ID FA1.
Error Message: The ID Data does not contain a contact with a Filer Unique ID (Field 1) as indicated by FA1.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:IDData)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.12.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.12.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.13
Requirement Description: ID Data (Fields 1-14) shall be checked for completeness.
Error Message: ID Data is incomplete Fields 1 through 14 are all required Fields.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.Field_1_FilerUniqueID IS NULL OR id.Field_2_CompanyName IS NULL OR id.Field_4_ContactName IS NULL OR id.Field_6_Email IS NULL
MERGE (v:Violation {RuleID: 'F.16.13', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'ID Data Incomplete (Fields 1-14)', v.Severity = 'Error'
MERGE (id)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.13.1
Requirement Description: The Contact Name (Field 4) for the designated Agent contact records shall be checked against eRegistration.
Error Message: The Contact Name (Field 4) for the designated Agent does not match the corresponding eRegistration record.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.13.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.13.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.14.1
Requirement Description: A filing shall contain one Seller as indicated by FS#.
Error Message: A filing must contain one Seller record as indicated by FS#.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.14.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.14.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.14.2
Requirement Description: A Seller shall contain one Contact included in the EQR: Otherwise, the system shall not validate the filing if no Contact or more than one Contact is included in the filing.
Error Message: A seller contact is missing in a Seller record. Must have one seller contact.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.14.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.14.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.14.4
Requirement Description: A Seller shall contain one or more eRegistered Contact Persons included in the EQR.
Error Message: A Seller must contain at least one eRegistered contact.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.14.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.14.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.14.5
Requirement Description: The Contact Name (Field 4) for the Seller contact shall be checked against eRegistration.
Error Message: The Contact Name (Field 4) for the Seller Contact does not match the corresponding eRegistration record.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.14.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.14.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.15
Requirement Description: The seller contact records shall be checked for completeness.
Error Message: Incomplete seller contact record {0}.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.15', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.15 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.16.3
Requirement Description: ID Data (Fields 1-14) shall contain one or more eRegistered Contact Persons included in the EQR.
Error Message: ID Data (Fields 1-14) must contain at least one eRegistered contact.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:IDData)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.16.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.16.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.17
Requirement Description: A contact person is not required for a buyer; however if it is provided, it must be valid.
Error Message: Please verify the Customer contact information, if provided, in the XML.
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.17', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.17 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.18
Requirement Description: If the FilingType of the Filing is "New" then all elements listed in the filing should also be "New". If the FilingType is New but some contents are "Replace", "Cancel", or "Merge", the entire filing should be rejected.
Error Message: A filing of type "New" must contain only elements of type "New". For more information on filing types, please see the latest version of the EQR Users Guide.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'New'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'F.16.18', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Overall filing type New requires all elements to be New', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.19
Requirement Description: If the FilingType of the Filing is "Replace" then all elements listed in the filing should also be "New". If the FilingType is "Replace" but some contents are "Replace", "Cancel", or "Merge", the entire filing should be rejected.
Error Message: A filing of type "Replace" must contain only elements of type "New" For more information on filing types; please see the latest version of the EQR Users Guide.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'Replace'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'F.16.19', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Overall filing type Replace requires all elements to be New', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.20.1
Requirement Description: If the FilingType of the Filing is "Delete" there should be no new contract or transaction data. Only the Seller and Filer Organizations should be listed in the file.
Error Message: A filing of type "Delete" must not contain any contract or transaction data. For more information on filing types please see the latest version of the EQR Users Guide
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.filing_type = 'Delete'
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'F.16.20.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Overall filing type Delete requires all elements to be New', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.20.2
Requirement Description: If the FilingType of the Filing is “Delete” there should be at least one organization that acts as a Filer and as a Seller (or two organizations, one as Filer and the second as Seller).
Error Message: A filing of type “Delete” requires at least one organization that acts as a Filer and as a Seller. The current filing contains no Organizations
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.20.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.20.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.20.3
Requirement Description: If the FilingType of the Filing is “Delete”, there should be no more than two organizations.
Error Message: A filing of type “Delete” cannot have more than two Organizations in it.
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.20.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.20.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.20.4
Requirement Description: If the FilingType of the Filing is “Delete”, there should be no new contract or transaction data. Only the Seller and Filer Organizations should be listed in the file.
Error Message: A filing of type “Delete” requires roles for Filer and Seller. The filing can contain exactly one Organization playing both roles, or exactly two Organizations, each playing one of the roles.
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.20.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.20.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.21
Requirement Description: The roles of a contact listed in an organization must correspond with the roles of the organization as reported in eRegistration.
Error Message: The role(s) of a contact person must match the role(s) of the Company
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct)-[:HAS_TRANSACTION]->(t:TransactionData)
WHERE t.Field_45_TransactionUniqueID IS NULL OR t.Field_63_ProductName IS NULL OR t.Field_64_Quantity IS NULL OR t.Field_65_Price IS NULL
MERGE (v:Violation {RuleID: 'F.16.21', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Transaction Data Incomplete (Fields 45-72)', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.23.1
Requirement Description: A filing must contain Companies playing a minimum of two roles, Seller and FilerAgent.
Error Message: A filing must have Companies playing a minimum of two roles, Seller and Agent. The current filing contains no organizations.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.23.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.23.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.23.2
Requirement Description: If an Organization is a Seller or FilerAgent, it must have a CID for the filing period. This is for filings dated after release of EQR 2013.
Error Message: CIDs are required for Sellers, and Filers.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.23.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.23.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.25
Requirement Description: No duplicate Uids across a filing for Organizations, Contacts, Contracts, required contract data and Transactions.
Error Message: Please ensure that all unique identifiers in Filer Unique Identifier (Field 1), Contract Unique Identifier (Field 15), and Transaction Unique Identifier (Field 45) are in fact unique and are not duplicated.
Severity: XSD
Type of Validation: XSD

WITH f, node.Field_45_TransactionUniqueID AS uid, collect(node) AS nodes
UNWIND nodes AS n

WITH f, node.Field_45_TransactionUniqueID AS uid, collect(node) AS nodes
UNWIND nodes AS n

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(node:TransactionData)
WITH f, node.Field_45_TransactionUniqueID AS uid, collect(node) AS nodes
WHERE size(nodes) > 1
UNWIND nodes AS n
MERGE (v:Violation {RuleID: 'F.16.25', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Duplicate ID: ' + uid, v.Severity = 'Error'
MERGE (n)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.26
Requirement Description: CIDs must be valid and active for the filing period, for Sellers, and FilerAgents.
Error Message: CID/DID (Company Identifier and Designated Identifier) will be checked to insure it is active and valid.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.26', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.26 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.27.1
Requirement Description: If the Organization.TransactionsReported ToIndexPricePublisher property is true, then there must be at least one Index Publisher listed.
Error Message: Data missing - The Seller’s TransactionsReportedToI ndexPriceP ublisher property is set to Yes, but there is no Index Publisher (Field 73) reported. If Field 13 is Y or Yes then 73 must be completed.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.27.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.27.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.27.2
Requirement Description: If for an organization, Organization.TransactionsReported ToIndexPricePublisher property is true, then the organization must be a Seller.
Error Message: Only Sellers (indicated by FS# in Field 1) should report to Price Publishers. Designated Agents (indicated by FA1 in Field 1) should not be reporting.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.27.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.27.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.27.3
Requirement Description: If the Organization has Index Publisher(s) then the organization must be a Seller.
Error Message: Only Sellers (indicated by FS# in Field 1) should report to Price Publishers Designated Agents (indicated by FA1 in Field 1) should not be reporting.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.27.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.27.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.27.4
Requirement Description: If there are one or more Index Publishers (Field 73) listed in Field 73, then the Seller’s TransactionsReportedToIndexPricePubli sher property must be true (Field 13) for the Seller.
Error Message: At Least one Index Publisher was listed in your filing; TransactionsReportedToI ndexPricePublisher (Field 13)property must be true (Y) (Field 13) Validate Transaction Filings>=Q3 2013 (Field 13)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.27.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.27.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.27.5
Requirement Description: If a filing is followed by one or more append filings, the appended data must have the same index publishers as the original filing. Alternatively, the appended data can be submitted with no index publisher information to skip checking.
Error Message: The index publishers do not match the index publishers submitted previously for the same quarter.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.27.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.27.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.16.28
Requirement Description: For each Index Publisher listed there must be information on the Transactions Reported by the Index publisher. Error message is “Error: The TransactionReported field of the Index Publisher is required.”
Error Message: The Index Reporting Data Transactions Reported (Field 74) is required.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.16.28', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.16.28 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.1
Requirement Description: Contract (Product) data validation Check: If Product Name is Energy or Booked  Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a critical error starting with 2005/Q1 data, but only a ‘warning’ (informational message) for earlier period.
Error Message: nan
Severity: nan
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.1.1
Requirement Description: Contract (Product) data validation Check: If Product Name is Energy or Booked  Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a ‘warning’ (informational message) before 2005/Q1.
Error Message: If Product Name (Field 30) is Energy or Booked Out Power, Rate Units cannot be $/MW or $/KW.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.1.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.1.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.1.2
Requirement Description: Contract (Product) data validation Check: If Product Name is Energy, Rate Units cannot be $/MW or $/KW. This will be considered a critical error starting with 2005/Q1 data.
Error Message: If Product Name (Field 30) is Energy, Rate Units cannot be $/MW or $/KW.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.1.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.1.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.2.1
Requirement Description: Transaction data validation check: If Product Name is Energy or Booked Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a ‘warning’ (informational message) before 2005/Q1.
Error Message: If Product Name (Field 63) is Energy or Booked Out Power, Rate Units (Field 66) cannot be $/MW or $/KW.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.2.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.2.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.2.2
Requirement Description: Transaction data validation check: If Product Name is Energy or Booked Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a critical error starting with 2005/Q1 data.
Error Message: If Product Name (Field 63) is Energy or Booked Out Power, Rate Units (Field 66) cannot be $/MW or $/KW.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.2.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.2.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.3.1
Requirement Description: Contract (Product) data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a ‘warning’ (informational message) before 2005/Q1.
Error Message: If Product Name (Field 30) is Capacity, Rate Units (Field 38) cannot be $/MWH or $/KWH.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.3.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.3.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.3.2
Requirement Description: Contract (Product) data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a critical error starting with 2005/Q1 data.
Error Message: If Product Name (Field 30) is Capacity, Rate Units (Field 38) cannot be $/MWH or $/KWH.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.3.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.3.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.4.1
Requirement Description: Transaction data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a ‘warning’ (informational message) before 2005Q1.
Error Message: If Product Name (Field 63) is Capacity, Rate Units (Field 66) cannot be $/MWH or $/KWH.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.4.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.4.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.4.2
Requirement Description: Transaction data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a critical error starting with 2005/Q1 data.
Error Message: If Product Name (Field63) is Capacity, Rate Units (Field 66) cannot be $/MWH or $/KWH.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.4.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.4.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.5
Requirement Description: Only Agent contacts listed are allowed to submit files. If the submitter is not listed in the file as an Assigned Agent, the file should be rejected.
Error Message: Only eRegistered and designated contacts are allowed to submit files. -- Contact persons attempting to submit EQR filings must have an active FERC ID and be a designated contact of the Seller Company. Your FERC ID was emailed to you when registering through eRegistration.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.8.1
Requirement Description: Transaction data validation check: If Rate Units (Field 66) is $/MWH and price is over $1,000.00 or under $1,000.” Validation text should state: “Warning: The Price (Field 65) you have entered for Transaction # exceeds $1,000.00/MWH” This check is only a ‘warning’ (informational) for all periods of data.
Error Message: The Price (Field 65) exceeds $1,000.00/MWH.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.8.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.8.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.8.2
Requirement Description: “Transaction data validation check: If Rate Units is $/KWH, and price is over $1.00 or under -$1.00.”
Error Message: The Price (Field 65) exceeds $1,000.00/MWH.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.8.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.8.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.17.8.3
Requirement Description: “Transaction data validation check: If Rate Units is cents/KWH, and price is over 100 cents or under -100 cents.” Validation text should state: “Warning: The Price you have entered for Transaction #nn is equivalent to over $1,000.00/MWH.”
Error Message: The Price (Field 65) exceeds$1,000.00/MWH.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.17.8.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.17.8.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.18.1.1
Requirement Description: The filing range shall be from 2002 to present - Check on start date is not earlier than 2002.
Error Message: The Filing Quarter (Field 14) cannot be before 2002.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.18.1.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.18.1.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.18.1.2
Requirement Description: The filing range shall be up to present - Check filing date is not beyond present day.
Error Message: The Filing Quarter (Field 14) cannot be in the future.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.18.1.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.18.1.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.18.2
Requirement Description: Submission validation check: The system shall not allow data to be filed for a period prior to the end of that period (e.g. 2004/Q4 cannot be submitted to FERC prior to Jan 1, 2005).
Error Message: A Filing cannot be submitted prior to the end of the filing period.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Filing)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.18.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.18.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.1
Requirement Description: The system shall validate zip codes, with sensitivity to the country where the zip code is based. Check missing zip.
Error Message: Contact Zip codes must be present in the address (Field 9).
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.2
Requirement Description: The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check on US contact address zip code.
Error Message: Invalid US zip code (Field 9)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.3
Requirement Description: The system shall validate state code length for US two letter state codes.
Error Message: Invalid state code in Contact State (Field 8). State codes must have exactly two characters.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.4
Requirement Description: The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check- Mexico contact address zip code.
Error Message: Invalid Mexico zip code (Field 9)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.5
Requirement Description: The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check on Great Britain contact address zip code.
Error Message: Invalid Great Britain zip code (Field 9)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.6
Requirement Description: The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check on Canada contact address zip code.
Error Message: Invalid Canada zip code (Field 9)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.19.1.7
Requirement Description: The system shall validate the Address - Check that the address is not null.
Error Message: The address cannot be null (Fields 6)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.19.1.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.19.1.7 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.1.1
Requirement Description: Seller Uid is blank.
Error Message: The Filer Unique Identifier (Field 1) must be provided
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.1.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.1.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.2.2
Requirement Description: The system shall reject an execution date that is empty or null for Period >= Q1 2004.
Error Message: Data missing from Contract Execution Date (Field 21) of contract terms.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.2.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.2.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.3
Requirement Description: If execution date <= 1/1/1900, then “Error: The Execution date needs to be after Jan 1, 1900. Date entered is {0}.”
Error Message: The Contract Execution Date (Field 21) must be after Jan 1, 1900
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.Field_21 IS NOT NULL AND item.Field_21 < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.20.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Date check failed for Field 21', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.4.2
Requirement Description: If CommencementDate is empty or null then “Error: Data missing from commencement date of contract terms.”
Error Message: Data missing from Commencement Date of Contract Terms (Field 22).
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.4.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.4.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.5
Requirement Description: If commencement date <= 1/1/1900 then “Error: The commencement date of contract terms needs to be after Jan 1, 1900. Date entered is {0}.”
Error Message: The Commencement Date of Contract Terms (Field 22) needs to be after Jan 1, 1900
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.Field_22 IS NOT NULL AND item.Field_22 < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.20.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Date check failed for Field 22', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.7
Requirement Description: If Termination Date <= 1/1/1900 then “Error: The Termination Date needs to be after Jan 1, 1900. Date entered is {0}.”
Error Message: The Contract Termination Date (Field 23) needs to be after Jan 1, 1900
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.Field_23 IS NOT NULL AND item.Field_23 < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.20.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Date check failed for Field 23', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.8
Requirement Description: ActualEnd date should be populated only if the end of the filing period is equal to or greater than the actual termination date. If the end of period is less than  ActualEnd date, then the field should be empty. “Error: The Actual termination date was provided even though the contract did not terminate during the filing period.”
Error Message: The Actual Termination Date (Field 24) was provided even though the contract has not yet been terminated.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.8', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.8 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.9
Requirement Description: ActualEnd <= 1/1/1900
Error Message: The Actual Termination Date (Field 24) needs to be after Jan 1, 1900
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.Field_24 IS NOT NULL AND item.Field_24 < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.20.9', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Date check failed for Field 24', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.11
Requirement Description: There are multiple buyers assigned to one contract or multiple sellers assigned to one contract.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.11', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.11 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.19
Requirement Description: If Seller is not registered with eTariff, then "Error: An attempt was made to submit a seller with nonexistent tariff. Seller name {0}, CID {1}, Guid UID {2}, Ferc Tariff Reference {3}." Not applicable to Non-public utilities.
Error Message: The Seller Company listed in Field 16 must have an active tariff for the filing period. A seller with an expired tariff was submitted.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.19', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.19 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.20
Requirement Description: If Seller is registered with eTariff but tariff expired before filing period end date,  then “Warning: Contract record contains a seller with an expired tariff. Seller name {0}, CID {1}, UID {2} and Ferc Tariff Reference {3}.”
Error Message: The Seller Company listed in Field 16 must have an active tariff for the filing period. A seller with an expired tariff was submitted.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:ContractTerms)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.20', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.20 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.21
Requirement Description: If Seller is registered with eTariff but tariff not found, then “Error: Attempt to submit a contract record containing a seller with unrecognized or cancelled tariff. Seller name {0}, CID {1}, UID {2} and FERC Tariff Reference {3}.”
Error Message: The Seller Company listed in Field 16 must have an active tariff for the filing period. A seller with an unrecognized or cancelled tariff was submitted. If filing for a non-public utility, please contact ferconlinesupport@ferc.gov.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.21', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.21 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.22
Requirement Description: Please confirm that you have entered the name of the FERC Tariff (Field 19) that authorizes you to make the sale.”
Error Message: A FERC Tariff Reference was not detected for the Seller Company. Please confirm the name of the FERC Tariff Reference (Field 19) that authorizes you to make the sale.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.22', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.22 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.20.23
Requirement Description: Duplicate Contract Unique Identifier (Field 15).
Error Message: It appears that there are duplicated Contract Unique Identifiers (Field 15).
Severity: XSD
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.20.23', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.20.23 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.2.1
Requirement Description: Each contract must be linked to a valid Seller.
Error Message: The Contract is linked to a Seller Company (Field 16) but the selling Company record is not correctly setup as a Seller.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.2.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.2.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.2.2
Requirement Description: Check Seller CID for validity.
Error Message: The Contract is linked to a Seller Company (Field 16) but the Seller Company record contains an invalid FERC CID.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.2.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.2.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.3.1
Requirement Description: Customer Company Name (Field 17) must be a valid customer.
Error Message: Customer Company Name (Field 47) is not found as an acceptable buyer in your Contract data (Field 17). Please reconcile the field(s).
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.3.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.3.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.3.2
Requirement Description: Customer Company Name (Field 17) is empty
Error Message: The Customer Company Name (Field 17) must not be blank.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.3.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.3.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.3.3
Requirement Description: Check Buyer CID for validity.
Error Message: The Contract is linked to a Customer (Buyer) Organization, but the Organization record contains an invalid Organization Number. Buyer Organization Number may be left blank or entered as the Company CID from the following list: http://www.ferc.gov/about/ offices/oemr/oemr- div/alletariffentities.xls.
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.3.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.3.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.5
Requirement Description: Contract Affiliate (Field 18) not Y or N.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.6
Requirement Description: If FERC_Tariff_Ref field is null or empty then “Error: Data missing from FERC Tariff Reference.”
Error Message: Data is missing from FERC Tariff Reference (Field 19).
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.7
Requirement Description: If ContractServiceAgreement is empty or null then “Error: Data missing from Contract Service Agreement.”
Error Message: Data missing from Contract Service Agreement ID (Field 20)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.7 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.12
Requirement Description: If extension provision description is null or empty, then “Error: Data missing from Extension Provision Description.”
Error Message: Data missing from Extension Provision Description (Field 25)
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.12', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.12 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.15
Requirement Description: ActualEnd > End of Period
Error Message: The Actual Termination Date (Field 24) reported is later than the end of the filing period. This field should be set only after the contract has been terminated.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.15', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.15 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.22
Requirement Description: Buyer name > 70 characters.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.22', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.22 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.31
Requirement Description: The Four Fields that create a distinct contract must be unique. This complex key is comprised of: Seller Company Name (Field 16), Customer Company Name (Field 17), FERC Tariff Reference (Field 19) and Contract Service Agreement ID (Field 20).
Error Message: Contract records must be unique.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:ContractTerms)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.31', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.31 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.21.32
Requirement Description: The maximum number of Contracts in a filing is 30,000, the maximum Contract Products per filing is 100,000, and the maximum Contract Products per Contract is 40,000
Error Message: Contract data that exceeds 30,000 records, or Contract Products that exceed 100,000 records could delay EQR file processing. Therefore, such filings will not be accepted using normal filing procedures. Also, the maximum allowed Contract Products per Contract is 40,000. A company that expects to exceed these limits should contact eqr@ferc.gov for assistance.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.21.32', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.21.32 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.22.2.2
Requirement Description: Empty or null Transaction Begin Date (Field 43)
Error Message: Data missing from Begin date (Field 43)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.22.2.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.22.2.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.22.3
Requirement Description: Disallow Begin Date <= Jan 1, 1900. Error message: “The Begin Date of the product needs to be after Jan 1, 1990.”
Error Message: The Begin date (Field 43) of the product needs to be after Jan 1, 1900
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.Field_43 IS NOT NULL AND item.Field_43 < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.22.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Date check failed for Field 43', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.22.4.2
Requirement Description: Do not allow empty or null End Date. (Field 44)
Error Message: Data missing from End date (Field 44).
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.22.4.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.22.4.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.22.5
Requirement Description: Disallow EndDate <= Jan 1, 1900. Error message:
Error Message: The End Date (Field 44) of the product needs to be after Jan 1, 1900
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.Field_44 IS NOT NULL AND item.Field_44 < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.22.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Date check failed for Field 44', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - If {property name} is not found in the database lookup table then error out. Class Name (Field 26) Term Name (Field 27) Increment Name (Field 28) Increment Peaking Name (Field 29) ProductType Name (Field 30) ProductName (Field 31) Units (Field 33)
Error Message: nan
Severity: See Break down
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1.1
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}”. Class Name
Error Message: Data missing from Class name ( Field 26)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1.2
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}”. Term Name
Error Message: Data missing from Term name (Field 27)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1.3
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}. Increment Name
Error Message: Data missing from Increment name (Field 28)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1.4
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}. Increment Peak Name
Error Message: Data missing from Increment Peaking name (Field 29)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1.5
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from  {property name}. ProductType
Error Message: Data missing from Product Type (Field 30)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.1.6
Requirement Description: Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from  {property name}. ProductName
Error Message: Data missing from Product Name (Field 31)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.1.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.1.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.2
Requirement Description: Allow empty or null Units (Field 33).
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.3
Requirement Description: If unit is not found in units lookup then must match data dictionary Appendix E
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.4
Requirement Description: Allow empty or null rate units.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.5
Requirement Description: If rate unit is not found in the rate units lookup, then “Rate Units value {0} is not a recognized value.”
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.6
Requirement Description: ProductType = “CR” then the valid product names are (1)Reassignment Agreement (2)Point-To-Point Agreement.
Error Message: The Product Name {0} (Field 31) is not valid. When Product Type Name (Field 30) is “CR” the valid product names are Reassignment Agreement or Point-To- Point Agreement.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.7
Requirement Description: Allow null or empty PORBA but disallow unknown values. Error message, “Point of Receipt Balancing Authority {0} is not a recognized value.”
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.7 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.8
Requirement Description: If PORBA = “HUB” then allow only known values for PORSL.
Error Message: The Contract Product Point of Receipt Specific Location (Field 40) is not valid for a Trading Hub, as indicated by the word “HUB” in Field 39.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.8', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.8 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.9
Requirement Description: Allow null or empty PODBA but disallow unknown values.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.9', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.9 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.10
Requirement Description: If PODBA = “HUB” then allow only known values for PODSL.
Error Message: The Contract Product Point of Delivery Specific Location (Field 42) is not valid for a trading hub as indicated by the word “HUB” in Field 41.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.10', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.10 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.21.2
Requirement Description: Confirm Contract Actual Termination Date >= Transaction End Date
Error Message: Contract Termination Date (Field 23) must be greater than or equal to the Transaction End Date (Field 52).
Severity: Warning
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.21.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.21.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.22
Requirement Description: If PODBA is anything but Hub, then you can type free text into PODSL If PODBA is Hub, then PODSL becomes a dropdown containing electric Hubs. In XML the PODSL and PODSLHub cannot be populated simultaneously.
Error Message: The XML PointOfDeliverySpecificLo cation and PointOfDeliverySpecificLo cationHub cannot be populated simultaneously (PODSL and PODSLHub cannot be populated simultaneously).
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.22', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.22 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.23
Requirement Description: In XML the PODSL and PODSLHub cannot be populated simultaneously. Similarly, the PORSL and PORSLHub cannot be populated simultaneously. If PODBA is Hub, then PODSL must be an electric Hub. If PORBA is Hub, then PORSL must be an electric Hub.
Error Message: If PODBA is HUB, then PODSLHub should contain a HUB from Appendix C and PODSL should be empty. If PORBA is HUB, then PORSLHub should contain a HUB from Appendix C and PORSL should be empty. The “SpecificLocation” and “SpecificLocationHub” should not be populated simultaneously.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.23', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.23 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.23.24
Requirement Description: Verify that at least one of the four rate fields is included: Rate (Field 34), Rate Minimum (Field 35), Rate Maximum (Field 36), Rate Description (Field 37).
Error Message: One of the four rate fields: Rate (Field 34), Rate Minimum (Field 35), Rate Maximum (Field 36), Rate Description (Field 37) must be included.
Severity: Error
Type of Validation: FERC Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.23.24', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.23.24 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.24.1
Requirement Description: Disallow empty or null Transaction Unique ID.
Error Message: The user assigned Transaction Unique ID (Field 45) cannot be blank.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.24.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.24.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.24.3
Requirement Description: Confirm EndDate > StartDate.
Error Message: The Transaction End Date (Field 52) must be greater than Transaction Begin Date (Field 51)
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(t:TransactionData)
WHERE t.Field_52_TransactionEndDate <= t.Field_51_TransactionBeginDate
MERGE (v:Violation {RuleID: 'F.24.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Temporal Error: End Date is not after Begin Date', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.24.4
Requirement Description: Confirm EndDate <= Period End Date and EndDate is provided.
Error Message: Transaction End Date (Field 52) must be less than or equal to the EQR report period End Date
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.24.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.24.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.24.5
Requirement Description: Confirm StartDate >= Period Start Date and StartDate is not null.
Error Message: Transaction Begin Date (Field 51) must be greater than or equal to the EQR report period Start Date
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.24.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.24.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.24.6
Requirement Description: Confirm that the Total Transaction Charge = (Price * Quantity) + TransmissionCharge. Also, (for Energy, Capacity, and Booked Out Power) Total Transaction Charge = (Standardized Price * Standardized Quantity) + TransmissionCharge. Confirm if units are in cents and if yes, then make the appropriate conversion to dollars before doing the math. Allow for a tolerance of +/-1% when equating.
Error Message: Total Transaction Charge (Field 70) must equal Price (Field 65) * Quantity (Field 64) + Total Transmission Charge (Field 69), with a +/-1% or $1 error tolerance. Also, (for Energy, Capacity, and Booked Out Power) Total Transaction Charge (Field 70) equal Standardized Price (Field 68) * Standardized Quantity (Field 67) + Total Transmission Charge (Field 69), with same tolerance. Note: Price (Field 65) * Quantity (Field 64) = Standardized Price (Field 68) * Standardized Quantity (Field 67).
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.24.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.24.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.24.15.1
Requirement Description: Check for duplicate transaction UIDs.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.24.15.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.24.15.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.1
Requirement Description: Disallow empty or null transaction UIDs.
Error Message: nan
Severity: XSD
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2
Requirement Description: Check that required fields are populated correctly. If {property name} is not found in the database lookup table then error out. Field, Property 59, Class Name 60, Term Name 61, Increment Name 62, Increment Peak Name 63, ProductName 55, RateUnits 56, TimeZone 57, PODBA
Error Message: nan
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.1
Requirement Description: Disallow empty Class Name.
Error Message: Class Name (Field 59) must be a recognized value. See Data Dictionary
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.2
Requirement Description: Disallow empty Term Name.
Error Message: Term Name (Field 60) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.3
Requirement Description: Disallow empty Increment Name.
Error Message: Increment Name (Field 61) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.4
Requirement Description: Disallow empty Increment Peaking Name.
Error Message: Increment Peaking name (Field 62) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.4', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.4 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.5
Requirement Description: Disallow empty Product Name.
Error Message: Product Name (Field 63) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.5 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.6
Requirement Description: Disallow empty Rate Units (Field 66)
Error Message: Rate Units (Field 66) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.6', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.6 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.7
Requirement Description: Disallow empty Time Zone.
Error Message: Time Zone (Field 56) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.7', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.7 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.2.8
Requirement Description: Disallow empty Point of Delivery Balancing Authority (Field 57).
Error Message: Point of Delivery Balancing Authority (Field 57) may not be empty or null
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.2.8', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.2.8 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.3
Requirement Description: If PODBA = “HUB” and PODSL-Hub is not found in the list of hubs then fail “Delivery Specific Location {0} is not valid (for Trading Hub).”
Error Message: The Point of Delivery Specific Location (Field 58) must be a valid non- empty string value.
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.13.2
Requirement Description: Confirm if Transaction is BookedOutPower and if buyer is an ISO. For Date>= 10/1/2006 reject file with error message.
Error Message: Offsetting transactions in RTO markets must be reported in the EQR in accordance with the Real Time/Day Ahead guidance document available at http://www.ferc.gov/docs- filing/eqr/news-help/real- time.pdf.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.13.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.13.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.14.1
Requirement Description: Confirm transaction quantity = 0. (or be null) If true and Date < 10/1/2006, then
Error Message: Sales should not have a Transaction Quantity (Field 64) equal to 0
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.14.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.14.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.15
Requirement Description: Confirm transaction quantity = 0. If true and Date > 10/1/2006, then check if totaltransactionCharge=0. If both are true, then fail with error message “Error: Sales cannot have both Quantity and Total Transaction Charge equal to 0.”
Error Message: Sales should not be reported if they have a Transaction Quantity (Field 64) and a Total Transaction Charge (Field 70) equal to 0.
Severity: Error
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.15', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.15 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.16
Requirement Description: Rule Name: Aggregate ISO Sales Detected Validation Calculation: Verify if the average interval of all of the transactions to an ISO in a given quarter is greater than 3 hours. Error Type: *Error Message: “It appears you are aggregating sales to an ISO: Buyers: <List of Buyers>“ Specific routine: Step 1 The Transactions are queried for transactions where the Transaction Start Date, Transaction End Date, Buyers Name (from the associated Contract) where the Transaction Product Name is ‘ENERGY’ and the Transaction Class Name is not ‘BA’ AND The Sellers name is the same as the Customer Company Name or ‘BOOKED OUT POWER’ Step 2 The results of Step 1 if any are queried for rows where the Buyers names are in the list of ISO AKAS Step 3 The results of Step 2 are queried grouped by Buyers for Buyers where the average duration of the Buyers transactions > 3 hours.
Error Message: It appears sales to an ISO are being aggregated.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.16', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.16 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.17.2
Requirement Description: Check for transaction records with duplicate data (warning). This is a complex key comprised of the following fields: Transaction Begin Date (Field 51) and Transaction End Date (Field 52).
Error Message: Duplicate transaction data found. The data cannot be exactly the same after grouping transactions by Transaction Begin Date (Field 51) and  Transaction End Date (Field 52). The data value fields were found to be identical. The data identification fields, Transaction Unique ID (Field 45) and  Transaction Unique Identifier (Field 50), were excluded from the comparison.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.17.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.17.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.18
Requirement Description: For FilingPeriod Q3 2013 and forward, If the product is not Booked Out Power, confirm that the Transaction Product (Field 63) is matched by an equivalent Product Name (Field 31). If Field 63 is Booked Out Power, Field 31 must be ENERGY or CAPACITY.
Error Message: Every transaction must have a corresponding contract. The Transaction Product (Field 63) must match a corresponding Contract Product Name (Field 31). The Transaction Product specified does not have a corresponding Contract for the same product and customer. If Field 63 is Booked Out Power, Field 31 must be ENERGY or CAPACITY.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct:ContractTerms)-[:HAS_TRANSACTION]->(t:TransactionData)
WHERE t.Field_63_ProductName <> ct.Field_30_ProductName
MERGE (v:Violation {RuleID: 'F.25.18', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Product Mismatch: Transaction (' + t.Field_63_ProductName + ') vs Contract (' + ct.Field_30_ProductName + ')', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.19
Requirement Description: Trade Date (Field 53) should not be null after Q3 2013.
Error Message: Trade Date (Field 53) should not be empty or null if the transaction was entered into on or after 7/1/2013.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.19', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.19 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.20
Requirement Description: Transaction Standardized Price is required after Q3 2013. For product names Energy, Capacity, and Booked Out Power only please specify the price in $/MWh if the product is Energy or Booked Out Power.
Error Message: Standardized Price (Field 68) should not be empty or null for Energy, Booked Out Power, or Capacity products if the transaction was entered into on or after 7/1/2013.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.20', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.20 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.21
Requirement Description: Transaction Type of Rate is required after Q3 2013.
Error Message: Type of Rate (Field 55) should not be empty or null if the transaction was entered into on or after 7/1/2013.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.21', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.21 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.24
Requirement Description: Transaction Standardized Quantity is required after Q3 2013. For product names Energy, Capacity, and Booked out Power only please specify the quantity in MWh if the product is energy or booked out power and specify the quantity in MW if the product is capacity.
Error Message: Standardized Quantity (Field 67) should not be empty or null for Energy, Booked Out power, or Capacity products if the transaction was entered into on, or after 7/1/2013.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.24', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.24 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.21.2
Requirement Description: If transaction Quantity is <= 0 Warning “Please confirm that transactions with negative or zero Quantity are correct”
Error Message: Please confirm that transactions with negative or zero Quantity (Field 64) are correct.
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.21.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.21.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.25.25
Requirement Description: In XML the PODSL and PODSLHub cannot be populated simultaneously. Similarly, the PORSL and PORSLHub cannot be populated simultaneously. If PODBA is Hub, then PODSL must be an electric Hub. If PORBA is Hub, then PORSL must be an electric Hub.
Error Message: If PODBA is HUB, then PODSLHub should contain a HUB from Appendix C and PODSL should be empty. If PORBA is HUB, then PORSLHub should contain a HUB from Appendix C and PORSL should be empty. The “SpecificLocation” and “SpecificLocationHub” should not be populated simultaneously.
Severity: Error
Type of Validation: XSD

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.25.25', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.25.25 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.41
Requirement Description: Valid Seller without a Tariff with FERC will use “NPU” as Tariff Reference.
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.41', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.41 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.41.1
Requirement Description: The system will Verify that Seller who entered “NPU” as Tariff Reference has been approved as such in Company Registration.
Error Message: The Seller is not listed in the FERC Company Registration System as a Non-Public Utility (NPU).
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.41.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.41.1 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.41.2
Requirement Description: The system shall generate a WARNING when the Tariff Reference is invalid.
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.41.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.41.2 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.41.3
Requirement Description: The system shall verify that all contracts belonging to a Seller, either have tariff references or are ALL declared as “NPU.”
Error Message: The Contracts specify the seller both as a Public Utility and a Non-Public Utility (NPU).
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.41.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.41.3 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.42
Requirement Description: Trade Date is required for transactions entered into on or after 7/1/2013
Error Message: Trade Date (Data Dictionary Field No. 53) is required WHEN Contract Execution Date (Data Dictionary Field No. 21) is on or after 7/1/2013. Please review transactions with Transaction Unique IDs <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.42', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.42 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.43
Requirement Description: Transaction Type of Rate is required for transactions entered into on or after 7/1/2013
Error Message: Transaction Type of Rate (Data Dictionary Field 55) is required when Contract Execution Date (Data Dictionary Field 21) is on or after 7/1/2013. Please review transactions with Transaction Unique IDs <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.43', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.43 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.44
Requirement Description: Standardized Price is required for products ENERGY, CAPACITY, and BOOKED OUT POWER for transactions entered into on or after 7/1/2013
Error Message: For product names ENERGY, CAPACITY, and BOOKED OUT POWER only. Standardized Price (Data Dictionary Field No. 68) is required when Contract Execution Date  (Data Dictionary Field 21) is on or after 7/1/2013. Please review transactions with Transaction Unique IDs <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.44', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.44 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.45
Requirement Description: Standardized Quantity is required for products ENERGY, CAPACITY, and BOOKED OUT POWER for transactions entered into on or after 7/1/2013
Error Message: For product names ENERGY, CAPACITY, and BOOKED OUT POWER only. Standardized Quantity (Data Dictionary Field No. 67) is required when Contract Execution Date  (Data Dictionary Field 21) is on or after 7/1/2013. Please review transactions with Transaction Unique IDs <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.45', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.45 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.46
Requirement Description: Rate Units must be equal to the Standardized Units (i.e., $/MWh or $/MW-Month) if Transaction Quantity equals Standardized Quantity.
Error Message: For product name Energy, if Transaction Quantity (Data Dictionary Field No. 64) is equal to Standardized Quantity (Data Dictionary Field No. 67), then Rate Units (Data Dictionary Field No. 66) must be $/MWh. For product name Capacity, if Transaction Quantity (Data Dictionary Field No. 64) is equal to Standardized Quantity (Data Dictionary Field No. 67), then Rate Units (Data Dictionary Field No. 66) must be $/MW-Month. For product name Booked Out Power, if Transaction Quantity (Data Dictionary Field No. 64) is equal to Standardized Quantity (Data Dictionary Field No. 67), then Rate Units (Data Dictionary Field No. 66) must be $/MWh or $/MW-month.  Please review transactions with Transaction Unique IDs  <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.46', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.46 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.47
Requirement Description: Rate Units must be equal to the Standardized Units (i.e., $/MWh or $/MW-Month) if Transaction Price equals Standardized Price.
Error Message: For product name Energy, if Price (Data Dictionary Field No. 65) is equal to Standardized Price (Data Dictionary Field No. 68), then Rate Units (Data Dictionary Field No. 66) must be $/MWh. For product name Capacity, if Price (Data Dictionary Field No. 65) is equal to Standardized Price (Data Dictionary Field No. 68), then Rate Units (Data Dictionary Field No. 66) must be $/MW-Month. For product name Booked Out Power, if Price (Data Dictionary Field No. 65) is equal to Standardized Price(Data Dictionary Field No. 68), then Rate Units (Data Dictionary Field No. 66) must be $/MWh or $/MW-month. Please review transactions with Transaction Unique IDs  <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.47', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.47 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.30.48
Requirement Description: Transaction Point of Delivery Specific Location (PODSL) is required
Error Message: Transaction Point of Delivery Specific Location (PODSL) (Data Dictionary Field No. 58) is required. Please review transactions with Transaction Unique IDs <list of first 10 EQR_Transaction_Uids>
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.30.48', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.30.48 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.31.01
Requirement Description: Any Seller for a given company must be either an Agent or Account Manager for that company.
Error Message: Please confirm that the Seller is an Agent or Account Manager.
Severity: Warning
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.31.01', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.31.01 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: F.31.02
Requirement Description: There should be only one Agent Contact per filing (hardened for XML submissions).
Error Message: Please confirm that the file you are submitting has only one Agent listed.
Severity: Error
Type of Validation: Data Check

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'F.31.02', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule F.31.02 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: Q3 2013
Requirement Description: “Yes” in this column indicates that the requirement is applicable to filings, beginning Q3 2013
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'Q3 2013', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule Q3 2013 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: Q4 2019
Requirement Description: “Yes” in this column indicates that the requirement is applicable to filings, beginning Q4 2019
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'Q4 2019', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule Q4 2019 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: Q1 2020
Requirement Description: “Yes” in this column indicates that the requirement is applicable to filings, beginning Q1 2020
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'Q1 2020', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule Q1 2020 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: Q2 2020
Requirement Description: “Yes” in this column indicates that the requirement is applicable to filings, beginning Q2 2020
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'Q2 2020', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule Q2 2020 validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: Data Check
Requirement Description: Validates business rules
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'Data Check', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule Data Check validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

## Original Req. ID: XSD
Requirement Description: Validates data types, relationships and constraints such as size, dates, or characters
Error Message: nan
Severity: nan
Type of Validation: nan

### cypher query
```cypher
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION|HAS_ID_DATA*1..3]->(item:Node)
WHERE item.invalid_condition // Manual review required for specific logic
MERGE (v:Violation {RuleID: 'XSD', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Rule XSD validation failure', v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v)
```

