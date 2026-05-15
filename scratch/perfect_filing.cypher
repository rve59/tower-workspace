// EQR COMPREHENSIVE PERFECT FILING BASELINE (Multi-Period & Multi-Part Support)
// This script satisfies all rules in EQR_Validation_Rules_2.xlsx, including cross-append checks.

// ==========================================
// 1. ORIGINAL FILING (2024Q1)
// ==========================================
CREATE (f1:Filing {
    CID: 'TEST_CORP',
    FilingYear: 2024,
    FilingQuarter: 1,
    FilingPeriod: '2024Q1',
    FilingType: 'New',
    Field_14_FilingQuarter: '2024-01-01'
})

CREATE (seller:IDData {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    Field_1_FilerUniqueID: 'FS_001',
    Field_2_CompanyName: 'Test Seller Corp',
    Field_13_ReportToIndex: 'Y' // Set to Y to trigger Index Publisher checks (F.16.27)
})
CREATE (f1)-[:HAS_ID_DATA]->(seller)

// Index Publisher for F.16.27 compliance
CREATE (ip1:IndexReporting {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    Field_73_IndexPublisher: 'Platts',
    Field_74_IndexPublication: 'Gas Daily'
})
CREATE (seller)-[:REPORTS_TO]->(ip1)

CREATE (c1:Contact {
    CID: 'TEST_CORP',
    Field_4_ContactName: 'John Doe',
    Field_6_Email: 'john.doe@testseller.com'
})
CREATE (seller)-[:HAS_CONTACT]->(c1)

// Contract 1: ENERGY
CREATE (con1:Contract {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    Field_15_ContractUniqueID: 'CON_ENERGY_001'
})
CREATE (f1)-[:HAS_CONTRACT]->(con1)

CREATE (ct1:ContractTerms {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    FilingType: 'New',
    Field_15_ContractUniqueID: 'CON_ENERGY_001',
    Field_30_ProductName: 'Energy',
    Field_38_RateUnits: '$/MWH',
    Field_21_ContractExecutionDate: '2023-12-01',
    Field_22_CommencementDate: '2024-01-01',
    Field_23_TerminationDate: '2025-12-31',
    Field_34_Rate: 45.50 // Satisfies Rule F.23.24 (At least one rate field)
})
CREATE (con1)-[:HAS_TERMS]->(ct1)

CREATE (t1:TransactionData {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    FilingType: 'New',
    Field_45_TransactionUniqueID: 'TX_ENG_001',
    Field_63_ProductName: 'Energy',
    Field_66_RateUnits: '$/MWH',
    Field_64_TransactionQuantity: 100,
    Field_65_TransactionPrice: 45.50,
    Field_70_TotalTransactionCharge: 4550.00, // Satisfies Rule F.24.6 (Quantity * Price)
    Field_51_TransactionBeginDate: '2024-01-15',
    Field_52_TransactionEndDate: '2024-01-16'
})
CREATE (ct1)-[:HAS_TRANSACTION]->(t1)

// Contract 2: CAPACITY (Satisfies Rule F.17.3.2 - Capacity Units)
CREATE (con2:Contract {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    Field_15_ContractUniqueID: 'CON_CAP_002'
})
CREATE (f1)-[:HAS_CONTRACT]->(con2)

CREATE (ct2:ContractTerms {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    FilingType: 'New',
    Field_15_ContractUniqueID: 'CON_CAP_002',
    Field_30_ProductName: 'Capacity',
    Field_38_RateUnits: '$/MW', // Correct for Capacity
    Field_22_CommencementDate: '2024-01-01'
})
CREATE (con2)-[:HAS_TERMS]->(ct2)

// ==========================================
// 2. APPEND FILING (For Rule F.16.27.5)
// ==========================================
CREATE (f2:Filing {
    CID: 'TEST_CORP',
    FilingYear: 2024,
    FilingQuarter: 1,
    FilingPeriod: '2024Q1',
    FilingType: 'Append'
})

CREATE (seller_append:IDData {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    Field_1_FilerUniqueID: 'FS_001',
    Field_13_ReportToIndex: 'Y'
})
CREATE (f2)-[:HAS_ID_DATA]->(seller_append)

// Must match Platts/Gas Daily to pass F.16.27.5
CREATE (ip2:IndexReporting {
    CID: 'TEST_CORP',
    FilingPeriod: '2024Q1',
    Field_73_IndexPublisher: 'Platts',
    Field_74_IndexPublication: 'Gas Daily'
})
CREATE (seller_append)-[:REPORTS_TO]->(ip2)
