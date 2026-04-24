import json
import os

data_dict = {
    "metadata": {
        "title": "EQR Data Dictionary",
        "version": "4.0",
        "docket": "RM23-9-000",
        "description": "Electronic Quarterly Reporting (EQR) Data Dictionary for regulatory filings to FERC."
    },
    "sections": {
        "identification_agent": {
             "title": "IDENTIFICATION DATA - AGENT",
             "fields": [
                 {"name": "Filer Unique Identifier", "required": "System Dependent", "definition": "Field and associated requirements are dependent on future system design."}
             ]
        },
        "identification_seller": {
            "title": "IDENTIFICATION DATA - SELLER",
            "fields": [
                {"name": "Seller", "required": "Y", "value_type": "Unrestricted text", "definition": "The name of the public utility authorized to make sales under FERC tariff or the name of the non-public utility required to file the EQR."},
                {"name": "Seller CID", "required": "Y", "value_type": "6-digit integer preceded by 'C'", "definition": "The Company Identifier (CID) obtained through the Commission’s Company Registration system."},
                {"name": "Seller Contact", "required": "Y", "value_type": "Unrestricted text", "definition": "The eRegistered person authorized by the Seller to be contacted about the Seller’s EQR."},
                {"name": "Seller Contact Phone", "required": "Y", "value_type": "Phone number", "definition": "The eRegistered phone number of the Seller Contact."},
                {"name": "Seller Contact Email", "required": "Y", "value_type": "Valid email address", "definition": "The eRegistered email of the Seller Contact."},
                {"name": "Filing Quarter", "required": "Y", "value_type": "1, 2, 3, or 4", "definition": "A one digit reference number to indicate the quarter for which the filing is submitted."},
                {"name": "Filing Year", "required": "Y", "value_type": "YYYY", "definition": "A four-digit reference number to indicate the year for which the data is submitted."},
                {"name": "Qualifying Facility", "required": "Y", "value_type": "Y (Yes), N (No)", "definition": "The Seller is a Qualifying Facility as defined under 18 C.F.R. §§ 292.201-211."},
                {"name": "Notes", "required": "Y (for refilings)", "value_type": "Unrestricted text", "definition": "Descriptive text accompanying all refilings, include a reason for refiling and a description or summary of revisions."}
            ]
        },
        "contract": {
            "title": "CONTRACT DATA",
            "fields": [
                {"name": "Contract Unique ID", "required": "System Dependent", "value_type": "Unrestricted text", "definition": "A unique identifier assigned by the Seller to each contract."},
                {"name": "Seller", "required": "Y", "value_type": "Unrestricted text", "definition": "Same as Seller in Identification Data."},
                {"name": "Customer is RTO/ISO", "required": "Y", "value_type": "Y (Yes), N (No)", "definition": "Whether the Customer is an RTO/ISO."},
                {"name": "Customer Company Name", "required": "Y", "value_type": "Unrestricted text", "definition": "The name of the purchaser of contract products and services."},
                {"name": "Contract Affiliate", "required": "Y", "value_type": "Y (Yes), N (No)", "definition": "Whether the Customer is an affiliate as defined under 18 C.F.R. § 35.36(a)(9)."},
                {"name": "FERC Tariff Reference", "required": "Y", "value_type": "Unrestricted text", "definition": "Cites the document that specifies the terms and conditions under which a Seller is authorized to make sales."},
                {"name": "Contract Service Agreement ID", "required": "Y", "value_type": "Unrestricted text", "definition": "A unique identifier assigned by the Seller to each service agreement."},
                {"name": "Contract Execution Date", "required": "Y", "value_type": "YYYYMMDD", "definition": "The date the contract is signed."},
                {"name": "Commencement Date of Contract Terms", "required": "Y", "value_type": "YYYYMMDD", "definition": "The date the terms of the contract reported became effective."},
                {"name": "Contract Termination Date", "required": "Conditional", "value_type": "YYYYMMDD", "definition": "The date that the contract expires."},
                {"name": "Actual Termination Date", "required": "Conditional", "value_type": "YYYYMMDD", "definition": "The date the contract actually terminates."},
                {"name": "Extension Provision Description", "required": "Y", "value_type": "Unrestricted text", "definition": "Description of terms that provide for the continuation of the contract."},
                {"name": "Class Name", "required": "Y", "value_type": "Enum", "definition": "Firm (F), Non-Firm (NF), Unit Power Sale (UP), or N/A."},
                {"name": "Term Name", "required": "Y", "value_type": "Enum", "definition": "Long Term (LT), Short Term (ST), Evergreen, or N/A."},
                {"name": "Increment Name", "required": "Y", "value_type": "Enum", "definition": "The duration over which a product is sold (5-min, 15-min, Hourly, Daily, Weekly, Monthly, Yearly, N/A)."},
                {"name": "Increment Peaking Name", "required": "Y", "value_type": "Enum", "definition": "Full Period (FP), Off-Peak (OP), Peak (P), or N/A."},
                {"name": "Product Type", "required": "Y", "value_type": "Enum", "definition": "Cost-Based (CB), Market-Based (MB), Transmission (T), Non-Public Utility (NPU), or Other."},
                {"name": "Product Name", "required": "Y", "value_type": "Enum (PRODUCT NAMES)", "definition": "Description of product being offered."},
                {"name": "Quantity", "required": "Conditional", "value_type": "Number (4 decimals)", "definition": "Quantity for the contract product identified."},
                {"name": "Units", "required": "Conditional", "value_type": "Enum (UNITS)", "definition": "Measure stated in the contract for the product sold."},
                {"name": "Rate", "required": "Conditional", "value_type": "Number (4 decimals)", "definition": "The charge for the product per unit as stated in the contract."},
                {"name": "Rate Minimum", "required": "Conditional", "value_type": "Number (4 decimals)", "definition": "Minimum rate to be charged if a range is specified."},
                {"name": "Rate Maximum", "required": "Conditional", "value_type": "Number (4 decimals)", "definition": "Maximum rate to be charged if a range is specified."},
                {"name": "Rate Description", "required": "Y", "value_type": "Unrestricted text", "definition": "Text description of rate or citation to FERC tariff."},
                {"name": "Rate Units", "required": "Conditional", "value_type": "Enum (RATE UNITS)", "definition": "Measure appropriate to the rate of the product sold."},
                {"name": "PORBAA", "required": "Conditional", "value_type": "Enum (BA List)", "definition": "Point of Receipt Balancing Authority Area."},
                {"name": "PORSL", "required": "Conditional", "value_type": "Unrestricted text", "definition": "Point of Receipt Specific Location."},
                {"name": "PODBAA", "required": "Conditional", "value_type": "Enum (BA List)", "definition": "Point of Delivery Balancing Authority Area."},
                {"name": "PODSL", "required": "Conditional", "value_type": "Unrestricted text", "definition": "Point of Delivery Specific Location."},
                {"name": "Begin Date", "required": "Conditional", "value_type": "YYYYMMDD", "definition": "First date for the sale of the product at the rate specified."},
                {"name": "End Date", "required": "Conditional", "value_type": "YYYYMMDD", "definition": "Last date for the sale of the product at the rate specified."},
                {"name": "Product Name Description", "required": "Conditional", "value_type": "Unrestricted text", "definition": "Description of the product(s) if selecting Other or Bundled."}
            ]
        },
        "transaction": {
            "title": "TRANSACTION DATA",
            "fields": [
                {"name": "Seller", "required": "Y", "value_type": "Unrestricted text", "definition": "Same as Seller in Identification Data."},
                {"name": "Customer Company Name", "required": "Y", "value_type": "Unrestricted text", "definition": "Same as Customer in Contract Data."},
                {"name": "Transaction Unique ID", "required": "System Dependent", "value_type": "Unrestricted text", "definition": "A unique identifier assigned by the Seller to each transaction."},
                {"name": "FERC Tariff Reference", "required": "Y", "value_type": "Unrestricted text", "definition": "Same as Contract Data."},
                {"name": "Contract Service Agreement ID", "required": "Y", "value_type": "Unrestricted text", "definition": "Same as Contract Data."},
                {"name": "Transaction Identifier", "required": "Y", "value_type": "Unrestricted text", "definition": "A reference number assigned by the Seller for each transaction."},
                {"name": "Transaction Begin Date", "required": "Y", "value_type": "YYYYMMDDHHMM", "definition": "First date and time the product is sold at the specified price."},
                {"name": "Transaction End Date", "required": "Y", "value_type": "YYYYMMDDHHMM", "definition": "Last date and time the product is sold at the specified price."},
                {"name": "Trade Date", "required": "Y", "value_type": "YYYYMMDD", "definition": "The date upon which the parties made the legally binding agreement on the price of a transaction."},
                {"name": "Type of Rate", "required": "Y", "value_type": "Enum", "definition": "Fixed, Formula, Electric Index, or RTO/ISO."},
                {"name": "Time Zone", "required": "Y", "value_type": "Enum (TIME ZONE)", "definition": "The time zone where the transaction takes place."},
                {"name": "PODBAA", "required": "Y", "value_type": "Enum (BA List)", "definition": "Point of Delivery Balancing Authority Area."},
                {"name": "PODSL", "required": "Conditional", "value_type": "Unrestricted text", "definition": "Point of Delivery Specific Location."},
                {"name": "Class Name", "required": "Y", "value_type": "Enum", "definition": "Same as Contract Data."},
                {"name": "Term Name", "required": "Y", "value_type": "Enum", "definition": "Long Term (LT) or Short Term (ST)."},
                {"name": "Increment Name", "required": "Y", "value_type": "Enum", "definition": "Same as Contract Data."},
                {"name": "Increment Peaking Name", "required": "Y", "value_type": "Enum", "definition": "Same as Contract Data."},
                {"name": "Product Name", "required": "Y", "value_type": "Enum (PRODUCT NAMES)", "definition": "Description of product being offered."},
                {"name": "Transaction Quantity", "required": "Y", "value_type": "Number (10 decimals)", "definition": "The quantity of the product in this transaction record."},
                {"name": "Price", "required": "Y", "value_type": "Number (10 decimals)", "definition": "Actual price charged for the product per unit."},
                {"name": "Rate Units", "required": "Y", "value_type": "Enum (RATE UNITS)", "definition": "Measure appropriate to the price of the product sold."},
                {"name": "Standardized Quantity", "required": "Y (selective)", "value_type": "Number (10 decimals)", "definition": "Quantity in MWh (Energy/Booked Out) or MW-Month (Capacity)."},
                {"name": "Standardized Price", "required": "Y (selective)", "value_type": "Number (10 decimals)", "definition": "Price in $/MWh (Energy/Booked Out) or $/MW-Month (Capacity)."},
                {"name": "Total Transmission Charge", "required": "Y", "value_type": "Number (2 decimals)", "definition": "Payments received for transmission services when explicitly identified."},
                {"name": "Total Transaction Charge", "required": "Y", "value_type": "Number (2 decimals)", "definition": "Transaction Quantity times Price plus Total Transmission Charge."}
            ]
        }
    },
    "enumerations": {
        "PRODUCT NAMES": [
            {"name": "BLACK START SERVICE", "contract": True, "transaction": False, "definition": "Service available after a system-wide blackout where a generator participates in system restoration activities without the availability of an outside electric supply (Ancillary Service)."},
            {"name": "BOOKED OUT POWER", "contract": False, "transaction": True, "definition": "Energy or capacity contractually committed bilaterally for delivery but not actually delivered due to some offsetting or countervailing trade (Transaction only)."},
            {"name": "BUNDLED", "contract": True, "transaction": True, "definition": "Services provided for two or more products listed in PRODUCT NAMES that are sold and priced together."},
            {"name": "CAPACITY", "contract": True, "transaction": True, "definition": "A quantity of demand that is charged on a $/KW or $/MW basis."},
            {"name": "CUSTOMER CHARGE", "contract": True, "transaction": True, "definition": "Fixed contractual charges assessed on a per customer basis that could include billing service."},
            {"name": "DIRECT ASSIGNMENT FACILITIES CHARGE", "contract": True, "transaction": False, "definition": "Charges for facilities or portions of facilities that are constructed or used for the sole use/benefit of a particular transmission customer."},
            {"name": "EMERGENCY ENERGY", "contract": True, "transaction": True, "definition": "Energy or capacity provided to another entity during critical situations."},
            {"name": "ENERGY", "contract": True, "transaction": True, "definition": "A quantity of electricity that is sold or transmitted over a period of time."},
            {"name": "ENERGY IMBALANCE", "contract": True, "transaction": True, "definition": "Service provided when a difference occurs between the scheduled and the actual delivery of energy to a load obligation (Ancillary Service)."},
            {"name": "ENERGY IMBALANCE MARKET", "contract": True, "transaction": True, "definition": "Product sold in a Commission-approved energy imbalance market for the purpose of balancing real-time supply and demand."},
            {"name": "EXCHANGE", "contract": True, "transaction": True, "definition": "Transaction whereby the receiver accepts delivery of energy for a supplier’s account and returns energy at times, rates, and in amounts as mutually agreed."},
            {"name": "FUEL CHARGE", "contract": True, "transaction": True, "definition": "Charge based on the cost or amount of fuel used for generation."},
            {"name": "GENERATOR IMBALANCE", "contract": True, "transaction": True, "definition": "Service provided when a difference occurs between the output of a generator located in the Transmission Provider’s Control Area and a delivery schedule."},
            {"name": "GRANDFATHERED BUNDLED", "contract": True, "transaction": False, "definition": "Services provided for bundled transmission, ancillary services and/or energy under contracts effective prior to Order No. 888’s OATTs."},
            {"name": "INTERCONNECTION AGREEMENT", "contract": True, "transaction": False, "definition": "Contract that provides the terms and conditions for a generator, etc., to physically connect to a transmission or distribution system."},
            {"name": "MEMBERSHIP AGREEMENT", "contract": True, "transaction": False, "definition": "Agreement to participate and be subject to rules of a system operator."},
            {"name": "MUST RUN AGREEMENT", "contract": True, "transaction": False, "definition": "An agreement that requires a unit to run."},
            {"name": "NEGOTIATED-RATE TRANSMISSION", "contract": True, "transaction": False, "definition": "Transmission performed under a negotiated rate contract (applies only to merchant transmission companies)."},
            {"name": "NETWORK INTEGRATION TRANSMISSION SERVICE AGREEMENT", "contract": True, "transaction": False, "definition": "Transmission service under contract providing network service."},
            {"name": "NETWORK OPERATING AGREEMENT", "contract": True, "transaction": False, "definition": "An executed agreement that contains the terms and conditions under which a network customer operates its facilities."},
            {"name": "OTHER", "contract": True, "transaction": False, "definition": "Any product or combination of products not listed in PRODUCT NAMES."},
            {"name": "POINT-TO-POINT AGREEMENT", "contract": True, "transaction": False, "definition": "Transmission service under contract between specified Points of Receipt and Delivery."},
            {"name": "PRIMARY FREQUENCY RESPONSE", "contract": True, "transaction": True, "definition": "Service provided as a stand-by resource to support autonomous, pre-programmed changes in output to rapidly arrest large changes in frequency."},
            {"name": "RAMPING", "contract": True, "transaction": True, "definition": "The ability to change the output of real power from a generating unit per some unit of time."},
            {"name": "REACTIVE SUPPLY & VOLTAGE CONTROL", "contract": True, "transaction": True, "definition": "Production or absorption of reactive power to maintain voltage levels on transmission systems (Ancillary Service)."},
            {"name": "REAL POWER TRANSMISSION LOSS", "contract": True, "transaction": True, "definition": "The loss of energy, resulting from transporting power over a transmission system."},
            {"name": "REGULATION & FREQUENCY RESPONSE", "contract": True, "transaction": True, "definition": "Service providing for continuous balancing of resources (generation and interchange) with load (Ancillary Service)."},
            {"name": "RENEWABLE ENERGY CREDIT (REC)", "contract": True, "transaction": True, "definition": "The sale of jurisdictional renewable energy credits (RECs)."},
            {"name": "REQUIREMENTS SERVICE", "contract": True, "transaction": True, "definition": "Firm, load-following power supply necessary to serve a specified share of customer’s aggregate load."},
            {"name": "SCHEDULE SYSTEM CONTROL & DISPATCH", "contract": True, "transaction": True, "definition": "Scheduling, confirming and implementing an interchange schedule (Ancillary Service)."},
            {"name": "SPINNING RESERVE", "contract": True, "transaction": True, "definition": "Unloaded synchronized generating capacity immediately responsive to system frequency (Ancillary Service)."},
            {"name": "SUPPLEMENTAL RESERVE", "contract": True, "transaction": True, "definition": "Service needed to serve load in system contingency, available with greater delay than SPINNING RESERVE (Ancillary Service)."},
            {"name": "SYSTEM OPERATING AGREEMENTS", "contract": True, "transaction": False, "definition": "Agreement that contains the terms and conditions under which a system or network customer shall operate its facilities."},
            {"name": "TOLLING ENERGY", "contract": True, "transaction": True, "definition": "Energy sold from a plant whereby the buyer provides fuel to a generator and receives power in return for pre-established fees."},
            {"name": "TRANSMISSION OWNERS AGREEMENT", "contract": True, "transaction": False, "definition": "Agreement that establishes terms and conditions under which a transmission owner transfers operational control over facilities."},
            {"name": "UPLIFT", "contract": True, "transaction": True, "definition": "A make-whole payment by an RTO/ISO to a utility."}
        ],
        "TIME ZONE": [
            {"code": "AD", "name": "Atlantic Daylight"},
            {"code": "AP", "name": "Atlantic Prevailing"},
            {"code": "AS", "name": "Atlantic Standard"},
            {"code": "CD", "name": "Central Daylight"},
            {"code": "CP", "name": "Central Prevailing"},
            {"code": "CS", "name": "Central Standard"},
            {"code": "ED", "name": "Eastern Daylight"},
            {"code": "EP", "name": "Eastern Prevailing"},
            {"code": "ES", "name": "Eastern Standard"},
            {"code": "MD", "name": "Mountain Daylight"},
            {"code": "MP", "name": "Mountain Prevailing"},
            {"code": "MS", "name": "Mountain Standard"},
            {"code": "PD", "name": "Pacific Daylight"},
            {"code": "PP", "name": "Pacific Prevailing"},
            {"code": "PS", "name": "Pacific Standard"}
        ],
        "UNITS": [
            {"code": "KV", "name": "Kilovolt"},
            {"code": "KVA", "name": "Kilovolt Amperes"},
            {"code": "KVR", "name": "Kilovar"},
            {"code": "KW", "name": "Kilowatt"},
            {"code": "KWH", "name": "Kilowatt Hour"},
            {"code": "KW-DAY", "name": "Kilowatt Day"},
            {"code": "KW-MO", "name": "Kilowatt Month"},
            {"code": "KW-WK", "name": "Kilowatt Week"},
            {"code": "KW-YR", "name": "Kilowatt Year"},
            {"code": "MVAR-YR", "name": "Megavar Year"},
            {"code": "MW", "name": "Megawatt"},
            {"code": "MWH", "name": "Megawatt Hour"},
            {"code": "MW-DAY", "name": "Megawatt Day"},
            {"code": "MW-MO", "name": "Megawatt Month"},
            {"code": "MW-WK", "name": "Megawatt Week"},
            {"code": "MW-YR", "name": "Megawatt Year"},
            {"code": "RKVA", "name": "Reactive Kilovolt Amperes"},
            {"code": "FLAT RATE", "name": "Flat Rate"}
        ],
        "RATE UNITS": [
            {"code": "$/KV", "name": "dollars per kilovolt"},
            {"code": "$/KVA", "name": "dollars per kilovolt amperes"},
            {"code": "$/KVR", "name": "dollars per kilovar"},
            {"code": "$/KW", "name": "dollars per kilowatt"},
            {"code": "$/KWH", "name": "dollars per kilowatt hour"},
            {"code": "$/KW-DAY", "name": "dollars per kilowatt day"},
            {"code": "$/KW-MO", "name": "dollars per kilowatt month"},
            {"code": "$/KW-WK", "name": "dollars per kilowatt week"},
            {"code": "$/KW-YR", "name": "dollars per kilowatt year"},
            {"code": "$/MW", "name": "dollars per megawatt"},
            {"code": "$/MWH", "name": "dollars per megawatt hour"},
            {"code": "$/MW-DAY", "name": "dollars per megawatt day"},
            {"code": "$/MW-MO", "name": "dollars per megawatt month"},
            {"code": "$/MW-WK", "name": "dollars per megawatt week"},
            {"code": "$/MW-YR", "name": "dollars per megawatt year"},
            {"code": "$/MVAR-YR", "name": "dollars per megavar year"},
            {"code": "$/RKVA", "name": "dollars per reactive kilovar amperes"},
            {"code": "CENTS", "name": "cents"},
            {"code": "CENTS/KVR", "name": "cents per kilovolt amperes"},
            {"code": "CENTS/KWH", "name": "cents per kilowatt hour"},
            {"code": "FLAT RATE", "name": "rate not specified in any other units"},
            {"code": "MILLS/KWH", "name": "mills per kilowatt hour"},
            {"code": "MW/MIN", "name": "megawatts per minute"},
            {"code": "MW/0.1 HZ", "name": "megawatts per 0.1 hertz"}
        ]
    }
}

output_path = "data/master/eqr_data_dictionary_v40.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w') as f:
    json.dump(data_dict, f, indent=4)

print(f"Data dictionary JSON generated at: {output_path}")
