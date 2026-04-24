# Master Rule Tracking: EQR Validation Rules

| Rule Code | Description | Feasibility | Implementation Status |
| :--- | :--- | :--- | :--- |
| D.3.9 | Refer to the “Filing Types” Tab For requirements of the manipulation of the Filing Types. | YES (Structural) | [ ] Pending |
| D.3.9.1 | For a filing with Filing.FilingType=New, all Contracts, Transactions and ContractProducts must also have FilingType=New. | YES (Structural) | [x] Active |
| D.3.9.2 | For a filing with Filing.FilingType=Replace, all Contracts, Transactions and ContractProducts must have FilingType=New. | YES (Structural) | [ ] Pending |
| D.3.9.3 | For a filing with Filing.FilingType=Delete, Contracts, Transactions and ContractProducts are not allowed. | YES (Structural) | [x] Active |
| D.3.9.4 | For a filing with Filing.FilingType=Merge, Contracts can be of any type. | YES (Structural) | [ ] Pending |
| D.3.9.5 | For a Contract Data file with Contract.FilingType=NoAction, the Transactions Data and Contract Products can have any type. | YES (Structural) | [ ] Pending |
| D.3.9.6 | For a Contract Data file with Contract.FilingType=New, all Transactions Data and ContractProducts must also have FilingType=New. | YES (Structural) | [x] Active |
| D.3.9.7 | For a Contract with Contract.FilingType=Replace, the Transactions and ContractProducts can have any type. | YES (Structural) | [ ] Pending |
| D.3.9.8 | For a Contract with Contract.FilingType=Delete, Transactions and ContractProducts are not allowed. | YES (Structural) | [x] Active |
| D.3.9.9 | Disallow XML delete option for external users | YES (Structural) | [ ] Pending |
| D.3.9.12 | The order of organizations in XML must be sequential | YES (Structural) | [ ] Pending |
| F.16.1 | The validations which result in a type: “Error” will result in a rejected Submission. | YES (Structural) | [ ] Pending |
| F.16.3 | A filing must have at least two rows of contact data in the ID Data. A filing that is submitted without at least two ID Data (Fields 1-14) rows populated - one with Filer Unique Identifier for a Seller (indicated by FS# in Field 1) and another with Filer Unique Identifier for agent (indicated by FA# in Field 1) - shall be rejected | YES (Structural) | [x] Active |
| F.16.3.1 | The Company Name (Field 2) shall be checked against the FERC Company Registration system. | SIMULATED (External Registry) | [x] Active |
| F.16.3.2 | The Seller Company Name (Field 16) shall be checked against the FERC Company Registration system. | SIMULATED (External Registry) | [x] Active |
| F.16.3.4 | The Organization Company Name (Field 2) for the seller contact row (i.e., FS# in Field 1) shall be checked against the name that was effective for the same CID in Company Registration at the end of the associated Filing Period. | SIMULATED (External Registry) | [ ] Pending |
| F.16.3.5 | The Seller Company Name (Field 16) shall be checked against the FERC Company Registration system history. The Contract Seller Company Name (Field 16) must be a name that that was effective for the same CID in Company Registration for all or part of the associated Filing Quarter. | SIMULATED (External Registry) | [ ] Pending |
| F.16.4.1 | The system shall check for the existence of duplicate ID Data (Fields 1-14). | YES (Parquet Dedup) | [ ] Pending |
| F.16.4.2 | The system shall check for the existence of duplicate Filer Unique Identifiers (Field 1). | YES (Parquet Dedup) | [ ] Pending |
| F.16.5 | The system shall check for the existence of duplicate Sellers. | YES (Parquet Dedup) | [ ] Pending |
| F.16.6 | The system shall check for the existence of duplicate Sellers. | YES (Parquet Dedup) | [ ] Pending |
| F.16.7 | The system shall not check for duplicate contacts. There is no certain way of verifying duplicate contacts; contacts are not eRegistered and two people can have the same name and work at the same employer. | YES (Parquet Dedup) | [ ] Pending |
| F.16.8 | The system shall check the validity of all email addresses with email Regex. | YES (Structural) | [x] Active |
| F.16.10 | A filing shall contain zero or more Contracts. | YES (Structural) | [ ] Pending |
| F.16.11 | A Contract shall contain required contract data (Fields 15-44): otherwise, the system will not validate the filing if required fields are not included in the filing. | YES (Structural) | [ ] Pending |
| F.16.12.1 | A filing shall contain only one ID Data contact record with Filer Unique ID FA1. | YES (Structural) | [x] Active |
| F.16.12.2 | A filing shall contain only one ID Data contact record with Filer Unique ID FA1. | YES (Structural) | [ ] Pending |
| F.16.13 | ID Data (Fields 1-14) shall be checked for completeness. | YES (Structural) | [ ] Pending |
| F.16.13.1 | The Contact Name (Field 4) for the designated Agent contact records shall be checked against eRegistration. | YES (Structural) | [ ] Pending |
| F.16.14.1 | A filing shall contain one Seller as indicated by FS#. | YES (Structural) | [x] Active |
| F.16.14.2 | A Seller shall contain one Contact included in the EQR: Otherwise, the system shall not validate the filing if no Contact or more than one Contact is included in the filing. | YES (Structural) | [ ] Pending |
| F.16.14.4 | A Seller shall contain one or more eRegistered Contact Persons included in the EQR. | YES (Structural) | [ ] Pending |
| F.16.14.5 | The Contact Name (Field 4) for the Seller contact shall be checked against eRegistration. | YES (Structural) | [ ] Pending |
| F.16.15 | The seller contact records shall be checked for completeness. | YES (Structural) | [ ] Pending |
| F.16.16.3 | ID Data (Fields 1-14) shall contain one or more eRegistered Contact Persons included in the EQR. | YES (Structural) | [ ] Pending |
| F.16.17 | A contact person is not required for a buyer; however if it is provided, it must be valid. | YES (Structural) | [ ] Pending |
| F.16.18 | If the FilingType of the Filing is "New" then all elements listed in the filing should also be "New". If the FilingType is New but some contents are "Replace", "Cancel", or "Merge", the entire filing should be rejected. | YES (Structural) | [ ] Pending |
| F.16.19 | If the FilingType of the Filing is "Replace" then all elements listed in the filing should also be "New". If the FilingType is "Replace" but some contents are "Replace", "Cancel", or "Merge", the entire filing should be rejected. | YES (Structural) | [ ] Pending |
| F.16.20.1 | If the FilingType of the Filing is "Delete" there should be no new contract or transaction data. Only the Seller and Filer Organizations should be listed in the file. | YES (Structural) | [ ] Pending |
| F.16.20.2 | If the FilingType of the Filing is “Delete” there should be at least one organization that acts as a Filer and as a Seller (or two organizations, one as Filer and the second as Seller). | YES (Structural) | [ ] Pending |
| F.16.20.3 | If the FilingType of the Filing is “Delete”, there should be no more than two organizations. | YES (Structural) | [ ] Pending |
| F.16.20.4 | If the FilingType of the Filing is “Delete”, there should be no new contract or transaction data. Only the Seller and Filer Organizations should be listed in the file. | YES (Structural) | [ ] Pending |
| F.16.21 | The roles of a contact listed in an organization must correspond with the roles of the organization as reported in eRegistration. | YES (Structural) | [ ] Pending |
| F.16.23.1 | A filing must contain Companies playing a minimum of two roles, Seller and FilerAgent. | YES (Structural) | [ ] Pending |
| F.16.23.2 | If an Organization is a Seller or FilerAgent, it must have a CID for the filing period. This is for filings dated after release of EQR 2013. | YES (Structural) | [ ] Pending |
| F.16.25 | No duplicate Uids across a filing for Organizations, Contacts, Contracts, required contract data and Transactions. | YES (Parquet Dedup) | [ ] Pending |
| F.16.26 | CIDs must be valid and active for the filing period, for Sellers, and FilerAgents. | YES (Structural) | [ ] Pending |
| F.16.27.1 | If the Organization.TransactionsReported ToIndexPricePublisher property is true, then there must be at least one Index Publisher listed. | YES (Direct Predicate) | [ ] Pending |
| F.16.27.2 | If for an organization, Organization.TransactionsReported ToIndexPricePublisher property is true, then the organization must be a Seller. | YES (Direct Predicate) | [ ] Pending |
| F.16.27.3 | If the Organization has Index Publisher(s) then the organization must be a Seller. | YES (Structural) | [ ] Pending |
| F.16.27.4 | If there are one or more Index Publishers (Field 73) listed in Field 73, then the Seller’s TransactionsReportedToIndexPricePubli sher property must be true (Field 13) for the Seller. | YES (Direct Predicate) | [ ] Pending |
| F.16.27.5 | If a filing is followed by one or more append filings, the appended data must have the same index publishers as the original filing. Alternatively, the appended data can be submitted with no index publisher information to skip checking. | CONTEXT (Historical Lake) | [ ] Pending |
| F.16.28 | For each Index Publisher listed there must be information on the Transactions Reported by the Index publisher. Error message is “Error: The TransactionReported field of the Index Publisher is required.” | YES (Structural) | [ ] Pending |
| F.17.1 | Contract (Product) data validation Check: If Product Name is Energy or Booked  Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a critical error starting with 2005/Q1 data, but only a ‘warning’ (informational message) for earlier period. | YES (Direct Predicate) | [ ] Pending |
| F.17.1.1 | Contract (Product) data validation Check: If Product Name is Energy or Booked  Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a ‘warning’ (informational message) before 2005/Q1. | YES (Direct Predicate) | [ ] Pending |
| F.17.1.2 | Contract (Product) data validation Check: If Product Name is Energy, Rate Units cannot be $/MW or $/KW. This will be considered a critical error starting with 2005/Q1 data. | YES (Direct Predicate) | [ ] Pending |
| F.17.2.1 | Transaction data validation check: If Product Name is Energy or Booked Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a ‘warning’ (informational message) before 2005/Q1. | YES (Direct Predicate) | [ ] Pending |
| F.17.2.2 | Transaction data validation check: If Product Name is Energy or Booked Out Power, Rate Units cannot be $/MW or $/KW. This will be considered a critical error starting with 2005/Q1 data. | YES (Direct Predicate) | [x] Active |
| F.17.3.1 | Contract (Product) data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a ‘warning’ (informational message) before 2005/Q1. | YES (Direct Predicate) | [ ] Pending |
| F.17.3.2 | Contract (Product) data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a critical error starting with 2005/Q1 data. | YES (Direct Predicate) | [ ] Pending |
| F.17.4.1 | Transaction data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a ‘warning’ (informational message) before 2005Q1. | YES (Direct Predicate) | [ ] Pending |
| F.17.4.2 | Transaction data validation check: If Product Name is Capacity, Rate Units cannot be $/MWH or $/KWH. This will be considered a critical error starting with 2005/Q1 data. | YES (Direct Predicate) | [x] Active |
| F.17.5 | Only Agent contacts listed are allowed to submit files. If the submitter is not listed in the file as an Assigned Agent, the file should be rejected. | YES (Structural) | [ ] Pending |
| F.17.8.1 | Transaction data validation check: If Rate Units (Field 66) is $/MWH and price is over $1,000.00 or under $1,000.” Validation text should state: “Warning: The Price (Field 65) you have entered for Transaction # exceeds $1,000.00/MWH” This check is only a ‘warning’ (informational) for all periods of data. | YES (Direct Predicate) | [x] Active |
| F.17.8.2 | “Transaction data validation check: If Rate Units is $/KWH, and price is over $1.00 or under -$1.00.” | YES (Direct Predicate) | [ ] Pending |
| F.17.8.3 | “Transaction data validation check: If Rate Units is cents/KWH, and price is over 100 cents or under -100 cents.” Validation text should state: “Warning: The Price you have entered for Transaction #nn is equivalent to over $1,000.00/MWH.” | YES (Direct Predicate) | [ ] Pending |
| F.18.1.1 | The filing range shall be from 2002 to present - Check on start date is not earlier than 2002. | YES (Structural) | [ ] Pending |
| F.18.1.2 | The filing range shall be up to present - Check filing date is not beyond present day. | YES (Structural) | [ ] Pending |
| F.18.2 | Submission validation check: The system shall not allow data to be filed for a period prior to the end of that period (e.g. 2004/Q4 cannot be submitted to FERC prior to Jan 1, 2005). | YES (Structural) | [ ] Pending |
| F.19.1.1 | The system shall validate zip codes, with sensitivity to the country where the zip code is based. Check missing zip. | YES (Structural) | [ ] Pending |
| F.19.1.2 | The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check on US contact address zip code. | YES (Structural) | [ ] Pending |
| F.19.1.3 | The system shall validate state code length for US two letter state codes. | YES (Structural) | [ ] Pending |
| F.19.1.4 | The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check- Mexico contact address zip code. | YES (Structural) | [ ] Pending |
| F.19.1.5 | The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check on Great Britain contact address zip code. | YES (Structural) | [ ] Pending |
| F.19.1.6 | The system shall validate zip codes, with sensitivity to the country where the zip code is based. Regex check on Canada contact address zip code. | YES (Structural) | [ ] Pending |
| F.19.1.7 | The system shall validate the Address - Check that the address is not null. | YES (Structural) | [ ] Pending |
| F.20.1.1 | Seller Uid is blank. | YES (Structural) | [ ] Pending |
| F.20.2.2 | The system shall reject an execution date that is empty or null for Period >= Q1 2004. | YES (Structural) | [ ] Pending |
| F.20.3 | If execution date <= 1/1/1900, then “Error: The Execution date needs to be after Jan 1, 1900. Date entered is {0}.” | YES (Structural) | [x] Active |
| F.20.4.2 | If CommencementDate is empty or null then “Error: Data missing from commencement date of contract terms.” | YES (Structural) | [ ] Pending |
| F.20.5 | If commencement date <= 1/1/1900 then “Error: The commencement date of contract terms needs to be after Jan 1, 1900. Date entered is {0}.” | YES (Structural) | [ ] Pending |
| F.20.7 | If Termination Date <= 1/1/1900 then “Error: The Termination Date needs to be after Jan 1, 1900. Date entered is {0}.” | YES (Structural) | [ ] Pending |
| F.20.8 | ActualEnd date should be populated only if the end of the filing period is equal to or greater than the actual termination date. If the end of period is less than  ActualEnd date, then the field should be empty. “Error: The Actual termination date was provided even though the contract did not terminate during the filing period.” | YES (Structural) | [ ] Pending |
| F.20.9 | ActualEnd <= 1/1/1900 | YES (Structural) | [ ] Pending |
| F.20.11 | There are multiple buyers assigned to one contract or multiple sellers assigned to one contract. | YES (Structural) | [ ] Pending |
| F.20.19 | If Seller is not registered with eTariff, then "Error: An attempt was made to submit a seller with nonexistent tariff. Seller name {0}, CID {1}, Guid UID {2}, Ferc Tariff Reference {3}." Not applicable to Non-public utilities. | YES (Direct Predicate) | [ ] Pending |
| F.20.20 | If Seller is registered with eTariff but tariff expired before filing period end date,  then “Warning: Contract record contains a seller with an expired tariff. Seller name {0}, CID {1}, UID {2} and Ferc Tariff Reference {3}.” | YES (Direct Predicate) | [ ] Pending |
| F.20.21 | If Seller is registered with eTariff but tariff not found, then “Error: Attempt to submit a contract record containing a seller with unrecognized or cancelled tariff. Seller name {0}, CID {1}, UID {2} and FERC Tariff Reference {3}.” | YES (Direct Predicate) | [ ] Pending |
| F.20.22 | Please confirm that you have entered the name of the FERC Tariff (Field 19) that authorizes you to make the sale.” | YES (Structural) | [ ] Pending |
| F.20.23 | Duplicate Contract Unique Identifier (Field 15). | YES (Parquet Dedup) | [ ] Pending |
| F.21.2.1 | Each contract must be linked to a valid Seller. | YES (Structural) | [x] Active |
| F.21.2.2 | Check Seller CID for validity. | YES (Structural) | [ ] Pending |
| F.21.3.1 | Customer Company Name (Field 17) must be a valid customer. | YES (Direct Predicate) | [ ] Pending |
| F.21.3.2 | Customer Company Name (Field 17) is empty | YES (Direct Predicate) | [ ] Pending |
| F.21.3.3 | Check Buyer CID for validity. | YES (Structural) | [ ] Pending |
| F.21.5 | Contract Affiliate (Field 18) not Y or N. | YES (Structural) | [x] Active |
| F.21.6 | If FERC_Tariff_Ref field is null or empty then “Error: Data missing from FERC Tariff Reference.” | YES (Direct Predicate) | [x] Active |
| F.21.7 | If ContractServiceAgreement is empty or null then “Error: Data missing from Contract Service Agreement.” | YES (Structural) | [ ] Pending |
| F.21.12 | If extension provision description is null or empty, then “Error: Data missing from Extension Provision Description.” | YES (Structural) | [ ] Pending |
| F.21.15 | ActualEnd > End of Period | YES (Structural) | [ ] Pending |
| F.21.22 | Buyer name > 70 characters. | YES (Structural) | [ ] Pending |
| F.21.31 | The Four Fields that create a distinct contract must be unique. This complex key is comprised of: Seller Company Name (Field 16), Customer Company Name (Field 17), FERC Tariff Reference (Field 19) and Contract Service Agreement ID (Field 20). | YES (Direct Predicate) | [ ] Pending |
| F.21.32 | The maximum number of Contracts in a filing is 30,000, the maximum Contract Products per filing is 100,000, and the maximum Contract Products per Contract is 40,000 | YES (Structural) | [ ] Pending |
| F.22.2.2 | Empty or null Transaction Begin Date (Field 43) | YES (Direct Predicate) | [ ] Pending |
| F.22.3 | Disallow Begin Date <= Jan 1, 1900. Error message: “The Begin Date of the product needs to be after Jan 1, 1990.” | YES (Structural) | [ ] Pending |
| F.22.4.2 | Do not allow empty or null End Date. (Field 44) | YES (Structural) | [ ] Pending |
| F.22.5 | Disallow EndDate <= Jan 1, 1900. Error message: | YES (Structural) | [ ] Pending |
| F.23.1 | Use the following pattern for the properties below: Disallow empty or null {property name} - If {property name} is not found in the database lookup table then error out. Class Name (Field 26) Term Name (Field 27) Increment Name (Field 28) Increment Peaking Name (Field 29) ProductType Name (Field 30) ProductName (Field 31) Units (Field 33) | YES (Direct Predicate) | [ ] Pending |
| F.23.1.1 | Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}”. Class Name | YES (Direct Predicate) | [ ] Pending |
| F.23.1.2 | Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}”. Term Name | YES (Direct Predicate) | [ ] Pending |
| F.23.1.3 | Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}. Increment Name | YES (Direct Predicate) | [ ] Pending |
| F.23.1.4 | Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from {property name}. Increment Peak Name | YES (Structural) | [ ] Pending |
| F.23.1.5 | Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from  {property name}. ProductType | YES (Structural) | [ ] Pending |
| F.23.1.6 | Use the following pattern for the properties below: Disallow empty or null {property name} - “Data missing from  {property name}. ProductName | YES (Structural) | [ ] Pending |
| F.23.2 | Allow empty or null Units (Field 33). | YES (Structural) | [ ] Pending |
| F.23.3 | If unit is not found in units lookup then must match data dictionary Appendix E | YES (Structural) | [ ] Pending |
| F.23.4 | Allow empty or null rate units. | YES (Direct Predicate) | [ ] Pending |
| F.23.5 | If rate unit is not found in the rate units lookup, then “Rate Units value {0} is not a recognized value.” | YES (Direct Predicate) | [x] Active |
| F.23.6 | ProductType = “CR” then the valid product names are (1)Reassignment Agreement (2)Point-To-Point Agreement. | YES (Direct Predicate) | [x] Active |
| F.23.7 | Allow null or empty PORBA but disallow unknown values. Error message, “Point of Receipt Balancing Authority {0} is not a recognized value.” | YES (Structural) | [ ] Pending |
| F.23.8 | If PORBA = “HUB” then allow only known values for PORSL. | YES (Structural) | [ ] Pending |
| F.23.9 | Allow null or empty PODBA but disallow unknown values. | YES (Structural) | [x] Active |
| F.23.10 | If PODBA = “HUB” then allow only known values for PODSL. | YES (Structural) | [ ] Pending |
| F.23.21.2 | Confirm Contract Actual Termination Date >= Transaction End Date | YES (Direct Predicate) | [ ] Pending |
| F.23.22 | If PODBA is anything but Hub, then you can type free text into PODSL If PODBA is Hub, then PODSL becomes a dropdown containing electric Hubs. In XML the PODSL and PODSLHub cannot be populated simultaneously. | YES (Structural) | [ ] Pending |
| F.23.23 | In XML the PODSL and PODSLHub cannot be populated simultaneously. Similarly, the PORSL and PORSLHub cannot be populated simultaneously. If PODBA is Hub, then PODSL must be an electric Hub. If PORBA is Hub, then PORSL must be an electric Hub. | YES (Structural) | [ ] Pending |
| F.23.24 | Verify that at least one of the four rate fields is included: Rate (Field 34), Rate Minimum (Field 35), Rate Maximum (Field 36), Rate Description (Field 37). | YES (Structural) | [ ] Pending |
| F.24.1 | Disallow empty or null Transaction Unique ID. | YES (Direct Predicate) | [x] Active |
| F.24.3 | Confirm EndDate > StartDate. | YES (Structural) | [x] Active |
| F.24.4 | Confirm EndDate <= Period End Date and EndDate is provided. | YES (Structural) | [ ] Pending |
| F.24.5 | Confirm StartDate >= Period Start Date and StartDate is not null. | YES (Structural) | [ ] Pending |
| F.24.6 | Confirm that the Total Transaction Charge = (Price * Quantity) + TransmissionCharge. Also, (for Energy, Capacity, and Booked Out Power) Total Transaction Charge = (Standardized Price * Standardized Quantity) + TransmissionCharge. Confirm if units are in cents and if yes, then make the appropriate conversion to dollars before doing the math. Allow for a tolerance of +/-1% when equating. | YES (Direct Predicate) | [x] Active |
| F.24.15.1 | Check for duplicate transaction UIDs. | YES (Parquet Dedup) | [x] Active |
| F.25.1 | Disallow empty or null transaction UIDs. | YES (Structural) | [ ] Pending |
| F.25.2 | Check that required fields are populated correctly. If {property name} is not found in the database lookup table then error out. Field, Property 59, Class Name 60, Term Name 61, Increment Name 62, Increment Peak Name 63, ProductName 55, RateUnits 56, TimeZone 57, PODBA | YES (Direct Predicate) | [ ] Pending |
| F.25.2.1 | Disallow empty Class Name. | YES (Direct Predicate) | [x] Active |
| F.25.2.2 | Disallow empty Term Name. | YES (Direct Predicate) | [x] Active |
| F.25.2.3 | Disallow empty Increment Name. | YES (Direct Predicate) | [x] Active |
| F.25.2.4 | Disallow empty Increment Peaking Name. | YES (Direct Predicate) | [x] Active |
| F.25.2.5 | Disallow empty Product Name. | YES (Direct Predicate) | [x] Active |
| F.25.2.6 | Disallow empty Rate Units (Field 66) | YES (Direct Predicate) | [x] Active |
| F.25.2.7 | Disallow empty Time Zone. | YES (Structural) | [x] Active |
| F.25.2.8 | Disallow empty Point of Delivery Balancing Authority (Field 57). | YES (Direct Predicate) | [x] Active |
| F.25.3 | If PODBA = “HUB” and PODSL-Hub is not found in the list of hubs then fail “Delivery Specific Location {0} is not valid (for Trading Hub).” | YES (Structural) | [ ] Pending |
| F.25.13.2 | Confirm if Transaction is BookedOutPower and if buyer is an ISO. For Date>= 10/1/2006 reject file with error message. | YES (Structural) | [ ] Pending |
| F.25.14.1 | Confirm transaction quantity = 0. (or be null) If true and Date < 10/1/2006, then | YES (Direct Predicate) | [x] Active |
| F.25.15 | Confirm transaction quantity = 0. If true and Date > 10/1/2006, then check if totaltransactionCharge=0. If both are true, then fail with error message “Error: Sales cannot have both Quantity and Total Transaction Charge equal to 0.” | YES (Direct Predicate) | [x] Active |
| F.25.16 | Rule Name: Aggregate ISO Sales Detected Validation Calculation: Verify if the average interval of all of the transactions to an ISO in a given quarter is greater than 3 hours. Error Type: *Error Message: “It appears you are aggregating sales to an ISO: Buyers: <List of Buyers>“ Specific routine: Step 1 The Transactions are queried for transactions where the Transaction Start Date, Transaction End Date, Buyers Name (from the associated Contract) where the Transaction Product Name is ‘ENERGY’ and the Transaction Class Name is not ‘BA’ AND The Sellers name is the same as the Customer Company Name or ‘BOOKED OUT POWER’ Step 2 The results of Step 1 if any are queried for rows where the Buyers names are in the list of ISO AKAS Step 3 The results of Step 2 are queried grouped by Buyers for Buyers where the average duration of the Buyers transactions > 3 hours. | YES (Direct Predicate) | [ ] Pending |
| F.25.17.2 | Check for transaction records with duplicate data (warning). This is a complex key comprised of the following fields: Transaction Begin Date (Field 51) and Transaction End Date (Field 52). | YES (Parquet Dedup) | [ ] Pending |
| F.25.18 | For FilingPeriod Q3 2013 and forward, If the product is not Booked Out Power, confirm that the Transaction Product (Field 63) is matched by an equivalent Product Name (Field 31). If Field 63 is Booked Out Power, Field 31 must be ENERGY or CAPACITY. | YES (Direct Predicate) | [x] Active |
| F.25.19 | Trade Date (Field 53) should not be null after Q3 2013. | YES (Direct Predicate) | [x] Active |
| F.25.20 | Transaction Standardized Price is required after Q3 2013. For product names Energy, Capacity, and Booked Out Power only please specify the price in $/MWh if the product is Energy or Booked Out Power. | YES (Direct Predicate) | [x] Active |
| F.25.21 | Transaction Type of Rate is required after Q3 2013. | YES (Direct Predicate) | [x] Active |
| F.25.24 | Transaction Standardized Quantity is required after Q3 2013. For product names Energy, Capacity, and Booked out Power only please specify the quantity in MWh if the product is energy or booked out power and specify the quantity in MW if the product is capacity. | YES (Direct Predicate) | [x] Active |
| F.25.21.2 | If transaction Quantity is <= 0 Warning “Please confirm that transactions with negative or zero Quantity are correct” | YES (Direct Predicate) | [x] Active |
| F.25.25 | In XML the PODSL and PODSLHub cannot be populated simultaneously. Similarly, the PORSL and PORSLHub cannot be populated simultaneously. If PODBA is Hub, then PODSL must be an electric Hub. If PORBA is Hub, then PORSL must be an electric Hub. | YES (Structural) | [ ] Pending |
| F.30.41 | Valid Seller without a Tariff with FERC will use “NPU” as Tariff Reference. | YES (Structural) | [ ] Pending |
| F.30.41.1 | The system will Verify that Seller who entered “NPU” as Tariff Reference has been approved as such in Company Registration. | SIMULATED (External Registry) | [ ] Pending |
| F.30.41.2 | The system shall generate a WARNING when the Tariff Reference is invalid. | YES (Structural) | [ ] Pending |
| F.30.41.3 | The system shall verify that all contracts belonging to a Seller, either have tariff references or are ALL declared as “NPU.” | YES (Structural) | [ ] Pending |
| F.30.42 | Trade Date is required for transactions entered into on or after 7/1/2013 | YES (Direct Predicate) | [ ] Pending |
| F.30.43 | Transaction Type of Rate is required for transactions entered into on or after 7/1/2013 | YES (Direct Predicate) | [ ] Pending |
| F.30.44 | Standardized Price is required for products ENERGY, CAPACITY, and BOOKED OUT POWER for transactions entered into on or after 7/1/2013 | YES (Direct Predicate) | [x] Active |
| F.30.45 | Standardized Quantity is required for products ENERGY, CAPACITY, and BOOKED OUT POWER for transactions entered into on or after 7/1/2013 | YES (Direct Predicate) | [x] Active |
| F.30.46 | Rate Units must be equal to the Standardized Units (i.e., $/MWh or $/MW-Month) if Transaction Quantity equals Standardized Quantity. | YES (Direct Predicate) | [ ] Pending |
| F.30.47 | Rate Units must be equal to the Standardized Units (i.e., $/MWh or $/MW-Month) if Transaction Price equals Standardized Price. | YES (Direct Predicate) | [ ] Pending |
| F.30.48 | Transaction Point of Delivery Specific Location (PODSL) is required | YES (Direct Predicate) | [x] Active |
| F.31.01 | Any Seller for a given company must be either an Agent or Account Manager for that company. | YES (Structural) | [ ] Pending |
| F.31.02 | There should be only one Agent Contact per filing (hardened for XML submissions). | YES (Structural) | [ ] Pending |
| Q3 2013 | “Yes” in this column indicates that the requirement is applicable to filings, beginning Q3 2013 | YES (Structural) | [ ] Pending |
| Q4 2019 | “Yes” in this column indicates that the requirement is applicable to filings, beginning Q4 2019 | YES (Structural) | [ ] Pending |
| Q1 2020 | “Yes” in this column indicates that the requirement is applicable to filings, beginning Q1 2020 | YES (Structural) | [ ] Pending |
| Q2 2020 | “Yes” in this column indicates that the requirement is applicable to filings, beginning Q2 2020 | YES (Structural) | [ ] Pending |
| Data Check | Validates business rules | YES (Structural) | [ ] Pending |
| XSD | Validates data types, relationships and constraints such as size, dates, or characters | YES (Structural) | [ ] Pending |
