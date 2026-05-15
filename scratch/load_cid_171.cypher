// 1. Create Filing Header
CREATE (f:Filing {
    CID: '171',
    FilingPeriod: '2025Q1',
    FilingPeriodStart: '2025-01-01',
    FilingPeriodEnd: '2025-03-31',
    FilingType: 'New'
})

// 2. Create ID Data (Intentional Error: F.16.27.1 - Missing IndexReporting relationship)
CREATE (s:IDData {
    Field_1_FilerUniqueID: 'FS_171',
    Field_2_CompanyName: 'Energy Corp 171',
    Field_13_ReportToIndex: 'Y',
    CID: '171',
    FilingPeriod: '2024Q1'
})
CREATE (a:IDData {
    Field_1_FilerUniqueID: 'FA_171',
    Field_2_CompanyName: 'Agency 171',
    CID: '171',
    FilingPeriod: '2024Q1'
})
CREATE (f)-[:HAS_ID_DATA]->(s)
CREATE (f)-[:HAS_ID_DATA]->(a)

// 3. Create Valid Contract (C_999)
CREATE (c999:Contract {Field_15_ContractUniqueID: 'C_999', CID: '171', FilingPeriod: '2025Q1'})
CREATE (ct999:ContractTerms {
    Field_15_ContractUniqueID: 'C_999',
    Field_30_ProductName: 'Energy',
    Field_38_RateUnits: '$/MWH',
    Field_22_CommencementDate: '2020-01-01',
    CID: '171',
    FilingPeriod: '2025Q1'
})
CREATE (f)-[:HAS_CONTRACT]->(c999)
CREATE (c999)-[:HAS_TERMS]->(ct999)

// 4. Create Contract with Intentional Error (F.17.1.2 - Energy product with Capacity units)
CREATE (c888:Contract {Field_15_ContractUniqueID: 'C_888', CID: '171', FilingPeriod: '2025Q1'})
CREATE (ct888:ContractTerms {
    Field_15_ContractUniqueID: 'C_888',
    Field_30_ProductName: 'Energy',
    Field_38_RateUnits: '$/MW', // INCORRECT
    Field_22_CommencementDate: '2021-01-01',
    CID: '171',
    FilingPeriod: '2025Q1'
})
CREATE (f)-[:HAS_CONTRACT]->(c888)
CREATE (c888)-[:HAS_TERMS]->(ct888)

// 5. Create Valid Transaction (TX_5555)
CREATE (t5555:TransactionData {
    Field_45_TransactionUniqueID: 'TX_5555',
    Field_63_ProductName: 'Energy',
    Field_64_Quantity: 500,
    Field_65_Price: 45.00,
    Field_70_TotalTransactionCharge: 22500.00,
    CID: '171',
    FilingPeriod: '2025Q1'
})
CREATE (ct999)-[:HAS_TRANSACTION]->(t5555)

// 6. Create Transaction with Intentional Error (F.25.18 - Product Mismatch)
CREATE (t6666:TransactionData {
    Field_45_TransactionUniqueID: 'TX_6666',
    Field_63_ProductName: 'Ancillary Services', // MISMATCH with C_999 (Energy)
    Field_64_Quantity: 100,
    Field_65_Price: 10.00,
    Field_70_TotalTransactionCharge: 1000.00,
    CID: '171',
    FilingPeriod: '2025Q1'
})
CREATE (ct999)-[:HAS_TRANSACTION]->(t6666)
