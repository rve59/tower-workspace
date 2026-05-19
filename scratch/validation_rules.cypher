
// D.3.9.1: Filing Type Check (New)
MATCH (f:Filing {FilingType: 'New'})
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.1', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header is New but component is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v);


// D.3.9.2: Filing Type Check (Replace)
MATCH (f:Filing {FilingType: 'Replace'})
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header is Replace but component is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v);


// D.3.9.3: Filing Type Check (Delete)
MATCH (f:Filing {FilingType: 'Delete'})
MATCH (f)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(item)
WHERE item.FilingType <> 'New'
MERGE (v:Violation {RuleID: 'D.3.9.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Filing header is Delete but component is ' + item.FilingType, v.Severity = 'Error'
MERGE (item)-[:HAS_VIOLATION]->(v);


// F.16.13: ID Data Completeness (Fields 1-14)
MATCH (f:Filing)-[:HAS_ID_DATA]->(id:IDData)
WHERE id.Field_1_FilerUniqueID IS NULL 
   OR id.Field_2_CompanyName IS NULL
   OR id.Field_4_ContactName IS NULL
   OR id.Field_6_Email IS NULL
MERGE (v:Violation {RuleID: 'F.16.13', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'ID Data Incomplete', v.Severity = 'Error'
MERGE (id)-[:HAS_VIOLATION]->(v);

// F.16.11: Contract Data Completeness (Fields 15-44)
MATCH (f:Filing)-[:HAS_CONTRACT]->(c:Contract)-[:HAS_TERMS]->(ct:ContractTerms)
WHERE ct.Field_15_ContractUniqueID IS NULL
   OR ct.Field_16_SellerCompanyName IS NULL
   OR ct.Field_17_CustomerCompanyName IS NULL
   OR ct.Field_30_ProductName IS NULL
MERGE (v:Violation {RuleID: 'F.16.11', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Contract Data Incomplete', v.Severity = 'Error'
MERGE (ct)-[:HAS_VIOLATION]->(v);

// F.16.21: Transaction Data Completeness (Fields 45-72)
MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct)-[:HAS_TRANSACTION]->(t:TransactionData)
WHERE t.Field_45_TransactionUniqueID IS NULL
   OR t.Field_63_ProductName IS NULL
   OR t.Field_64_Quantity IS NULL
   OR t.Field_65_Price IS NULL
MERGE (v:Violation {RuleID: 'F.16.21', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Transaction Data Incomplete', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v);


// F.25.18: Transaction-to-Contract Product Name Match
MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct:ContractTerms)-[:HAS_TRANSACTION]->(t:TransactionData)
WHERE t.Field_63_ProductName <> ct.Field_30_ProductName
MERGE (v:Violation {RuleID: 'F.25.18', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Product Mismatch: Transaction (' + t.Field_63_ProductName + ') vs Contract (' + ct.Field_30_ProductName + ')', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v);

// F.17.1.2: Energy Product Unit Check
MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct:ContractTerms)
WHERE ct.Field_30_ProductName = 'Energy' AND ct.Field_38_RateUnits IN ['$/MW', '$/KW']
MERGE (v:Violation {RuleID: 'F.17.1.2', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Invalid Units: Energy product cannot use Capacity units ($/MW or $/KW)', v.Severity = 'Error'
MERGE (ct)-[:HAS_VIOLATION]->(v);


// F.24.3: Transaction Date Sequence
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(t:TransactionData)
WHERE t.Field_52_TransactionEndDate <= t.Field_51_TransactionBeginDate
MERGE (v:Violation {RuleID: 'F.24.3', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Temporal Error: End Date is not after Begin Date', v.Severity = 'Error'
MERGE (t)-[:HAS_VIOLATION]->(v);

// F.20.5: Commencement Date Bound
MATCH (f:Filing)-[:HAS_CONTRACT]->(c)-[:HAS_TERMS]->(ct:ContractTerms)
WHERE ct.Field_22_CommencementDate < '1900-01-01'
MERGE (v:Violation {RuleID: 'F.20.5', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Commencement Date is before 1900', v.Severity = 'Error'
MERGE (ct)-[:HAS_VIOLATION]->(v);


// F.16.25: Transaction ID Uniqueness
MATCH (f:Filing)-[:HAS_CONTRACT|HAS_TERMS|HAS_TRANSACTION*1..3]->(t:TransactionData)
WITH f, t.Field_45_TransactionUniqueID AS tid, collect(t) AS nodes
WHERE size(nodes) > 1
UNWIND nodes AS node
MERGE (v:Violation {RuleID: 'F.16.25', CID: f.CID, FilingPeriod: f.FilingPeriod})
ON CREATE SET v.Message = 'Duplicate Transaction Unique ID: ' + tid, v.Severity = 'Error'
MERGE (node)-[:HAS_VIOLATION]->(v);