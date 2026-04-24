from __future__ import annotations
from enum import Enum
from typing import Optional, List, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, datetime

# --- ENUMS (Based on Appendices) ---

class FilingQuarter(int, Enum):
    Q1 = 1
    Q2 = 2
    Q3 = 3
    Q4 = 4

class ClassName(str, Enum):
    F = "F"
    NF = "NF"
    UP = "UP"
    NA = "N/A"

class TermName(str, Enum):
    LT = "LT"
    ST = "ST"
    EVERGREEN = "Evergreen"
    MASTER = "Master Agreement"
    NA = "N/A"

class IncrementName(str, Enum):
    FIVE_MIN = "5 - Five-Minute"
    FIFTEEN_MIN = "15 - Fifteen-Minute"
    HOURLY = "H - Hourly"
    DAILY = "D - Daily"
    WEEKLY = "W - Weekly"
    MONTHLY = "M - Monthly"
    YEARLY = "Y - Yearly"
    NA = "N/A"

class IncrementPeakingName(str, Enum):
    FP = "FP"
    OP = "OP"
    P = "P"
    NA = "N/A"

class ProductType(str, Enum):
    CB = "CB"
    MB = "MB"
    T = "T"
    NPU = "NPU"
    OTHER = "Other"

class TypeOfRate(str, Enum):
    FIXED = "Fixed"
    FORMULA = "Formula"
    ELECTRIC_INDEX = "Electric Index"
    RTO_ISO = "RTO/ISO"

class TimeZone(str, Enum):
    AD = "AD"
    AP = "AP"
    AS = "AS"
    CD = "CD"
    CP = "CP"
    CS = "CS"
    ED = "ED"
    EP = "EP"
    ES = "ES"
    MD = "MD"
    MP = "MP"
    MS = "MS"
    PD = "PD"
    PP = "PP"
    PS = "PS"

class Unit(str, Enum):
    KV = "KV"
    KVA = "KVA"
    KVR = "KVR"
    KW = "KW"
    KWH = "KWH"
    KW_DAY = "KW-DAY"
    KW_MO = "KW-MO"
    KW_WK = "KW-WK"
    KW_YR = "KW-YR"
    MVAR_YR = "MVAR-YR"
    MW = "MW"
    MWH = "MWH"
    MW_DAY = "MW-DAY"
    MW_MO = "MW-MO"
    MW_WK = "MW-WK"
    MW_YR = "MW-YR"
    RKVA = "RKVA"
    FLAT_RATE = "FLAT RATE"

class RateUnit(str, Enum):
    D_KV = "$/KV"
    D_KVA = "$/KVA"
    D_KVR = "$/KVR"
    D_KW = "$/KW"
    D_KWH = "$/KWH"
    D_KW_DAY = "$/KW-DAY"
    D_KW_MO = "$/KW-MO"
    D_KW_WK = "$/KW-WK"
    D_KW_YR = "$/KW-YR"
    D_MW = "$/MW"
    D_MWH = "$/MWH"
    D_MW_DAY = "$/MW-DAY"
    D_MW_MO = "$/MW-MO"
    D_MW_WK = "$/MW-WK"
    D_MW_YR = "$/MW-YR"
    D_MVAR_YR = "$/MVAR-YR"
    D_RKVA = "$/RKVA"
    CENTS = "CENTS"
    C_KVA = "CENTS/KVA"
    C_KWH = "CENTS/KWH"
    FLAT_RATE = "FLAT RATE"
    MILLS_KWH = "MILLS/KWH"
    MW_MIN = "MW/MIN"
    MW_HZ = "MW/0.1 HZ"

class ProductName(str, Enum):
    BLACK_START = "BLACK START SERVICE"
    BOOKED_OUT = "BOOKED OUT POWER"
    BUNDLED = "BUNDLED"
    CAPACITY = "CAPACITY"
    CUSTOMER_CHARGE = "CUSTOMER CHARGE"
    DIRECT_ASSIGNMENT = "DIRECT ASSIGNMENT FACILITIES CHARGE"
    EMERGENCY_ENERGY = "EMERGENCY ENERGY"
    ENERGY = "ENERGY"
    ENERGY_IMBALANCE = "ENERGY IMBALANCE"
    EIM = "ENERGY IMBALANCE MARKET"
    EXCHANGE = "EXCHANGE"
    FUEL_CHARGE = "FUEL CHARGE"
    GENERATOR_IMBALANCE = "GENERATOR IMBALANCE"
    GRANDFATHERED_BUNDLED = "GRANDFATHERED BUNDLED"
    INTERCONNECTION = "INTERCONNECTION AGREEMENT"
    MEMBERSHIP = "MEMBERSHIP AGREEMENT"
    MUST_RUN = "MUST RUN AGREEMENT"
    NEGOTIATED_RATE_TRANS = "NEGOTIATED-RATE TRANSMISSION"
    NITS = "NETWORK INTEGRATION TRANSMISSION SERVICE AGREEMENT"
    NOA = "NETWORK OPERATING AGREEMENT"
    OTHER = "OTHER"
    PTP = "POINT-TO-POINT AGREEMENT"
    PRIMARY_FREQ = "PRIMARY FREQUENCY RESPONSE"
    RAMPING = "RAMPING"
    REACTIVE = "REACTIVE SUPPLY & VOLTAGE CONTROL"
    LOSSES = "REAL POWER TRANSMISSION LOSS"
    REGULATION = "REGULATION & FREQUENCY RESPONSE"
    REC = "RENEWABLE ENERGY CREDIT (REC)"
    REQUIREMENTS = "REQUIREMENTS SERVICE"
    SCHEDULE = "SCHEDULE SYSTEM CONTROL & DISPATCH"
    SPINNING = "SPINNING RESERVE"
    SUPPLEMENTAL = "SUPPLEMENTAL RESERVE"
    SOA = "SYSTEM OPERATING AGREEMENTS"
    TOLLING = "TOLLING ENERGY"
    TOA = "TRANSMISSION OWNERS AGREEMENT"
    UPLIFT = "UPLIFT"

# --- CORE MODELS ---

class EQRBaseModel(BaseModel):
    class Config:
        use_enum_values = True

class IdentificationData(EQRBaseModel):
    # Filer Unique ID is typically handled by the system
    seller_name: str = Field(..., alias="Seller")
    seller_cid: str = Field(..., alias="Seller CID")
    seller_contact: str = Field(..., alias="Seller Contact")
    seller_contact_phone: str = Field(..., alias="Seller Contact Phone")
    seller_contact_email: str = Field(..., alias="Seller Contact Email")
    filing_quarter: FilingQuarter = Field(..., alias="Filing Quarter")
    filing_year: int = Field(..., alias="Filing Year", ge=2000)
    qualifying_facility: str = Field(..., alias="Qualifying Facility")  # Y or N
    notes: Optional[str] = Field(None, alias="Notes")

    @field_validator("seller_cid")
    def validate_cid(cls, v):
        if not v.startswith("C") or not v[1:].isdigit() or len(v) != 7:
             raise ValueError("Seller CID must be a 6-digit integer preceded by 'C'")
        return v

    @field_validator("qualifying_facility")
    def validate_yn(cls, v):
        if v.upper() not in ["Y", "N"]:
            raise ValueError("Must be 'Y' or 'N'")
        return v.upper()

class IndexData(EQRBaseModel):
    seller_name: str = Field(..., alias="Seller")
    seller_cid: str = Field(..., alias="Seller CID")
    filer_name: str = Field(..., alias="Filer")
    filer_cid: str = Field(..., alias="Filer CID")
    contact_name: str = Field(..., alias="Contact Name")
    contact_phone: str = Field(..., alias="Contact Phone")
    contact_email: str = Field(..., alias="Contact Email")
    filing_year: int = Field(..., alias="Filing Year")
    filing_quarter: int = Field(..., alias="Filing Quarter")
    technical_id: str = Field(..., alias="Technical ID")

class ContractData(EQRBaseModel):
    contract_unique_id: str = Field(..., alias="Contract Unique ID")
    seller: str = Field(..., alias="Seller")
    customer_is_rto_iso: str = Field(..., alias="Customer is RTO/ISO")  # Y or N
    customer_company_name: str = Field(..., alias="Customer Company Name")
    contract_affiliate: str = Field(..., alias="Contract Affiliate")  # Y or N
    ferc_tariff_reference: str = Field(..., alias="FERC Tariff Reference")
    contract_service_agreement_id: str = Field(..., alias="Contract Service Agreement ID")
    execution_date: str = Field(..., alias="Contract Execution Date")  # YYYYMMDD
    commencement_date: str = Field(..., alias="Commencement Date of Contract Terms")  # YYYYMMDD
    termination_date: Optional[str] = Field(None, alias="Contract Termination Date")
    actual_termination_date: Optional[str] = Field(None, alias="Actual Termination Date")
    extension_provision: str = Field(..., alias="Extension Provision Description")
    class_name: ClassName = Field(..., alias="Class Name")
    term_name: TermName = Field(..., alias="Term Name")
    increment_name: IncrementName = Field(..., alias="Increment Name")
    increment_peaking_name: IncrementPeakingName = Field(..., alias="Increment Peaking Name")
    product_type: ProductType = Field(..., alias="Product Type")
    product_name: str = Field(..., alias="Product Name")  # Can be Enum or Description
    quantity: Optional[float] = Field(None, alias="Quantity")
    units: Optional[Unit] = Field(None, alias="Units")
    rate: Optional[float] = Field(None, alias="Rate")
    rate_minimum: Optional[float] = Field(None, alias="Rate Minimum")
    rate_maximum: Optional[float] = Field(None, alias="Rate Maximum")
    rate_description: str = Field(..., alias="Rate Description")
    rate_units: Optional[RateUnit] = Field(None, alias="Rate Units")
    porbaa: Optional[str] = Field(None, alias="PORBAA")
    porsl: Optional[str] = Field(None, alias="PORSL")
    podbaa: Optional[str] = Field(None, alias="PODBAA")
    podsl: Optional[str] = Field(None, alias="PODSL")
    begin_date: Optional[str] = Field(None, alias="Begin Date")
    end_date: Optional[str] = Field(None, alias="End Date")
    product_name_description: Optional[str] = Field(None, alias="Product Name Description")

    @model_validator(mode="after")
    def validate_conditional_description(self) -> "ContractData":
        if self.product_name in ["Other", "Bundled"] and not self.product_name_description:
            raise ValueError("Product Name Description is required if Product Name is Other or Bundled")
        return self

class TransactionData(EQRBaseModel):
    seller: str = Field(..., alias="Seller")
    customer_company_name: str = Field(..., alias="Customer Company Name")
    contract_unique_id: str = Field(..., alias="Contract Unique ID")
    transaction_unique_id: str = Field(..., alias="Transaction Unique ID")
    ferc_tariff_reference: str = Field(..., alias="FERC Tariff Reference")
    contract_service_agreement_id: str = Field(..., alias="Contract Service Agreement ID")
    transaction_identifier: str = Field(..., alias="Transaction Identifier")
    transaction_begin_date: str = Field(..., alias="Transaction Begin Date") # YYYYMMDDHHMM
    transaction_end_date: str = Field(..., alias="Transaction End Date") # YYYYMMDDHHMM
    trade_date: str = Field(..., alias="Trade Date") # YYYYMMDD
    type_of_rate: TypeOfRate = Field(..., alias="Type of Rate")
    time_zone: TimeZone = Field(..., alias="Time Zone")
    podbaa: str = Field(..., alias="PODBAA")
    podsl: Optional[str] = Field(None, alias="PODSL")
    class_name: ClassName = Field(..., alias="Class Name")
    term_name: TermName = Field(..., alias="Term Name")
    increment_name: IncrementName = Field(..., alias="Increment Name")
    increment_peaking_name: IncrementPeakingName = Field(..., alias="Increment Peaking Name")
    product_name: str = Field(..., alias="Product Name")
    transaction_quantity: float = Field(..., alias="Transaction Quantity")
    price: float = Field(..., alias="Price")
    rate_units: RateUnit = Field(..., alias="Rate Units")
    standardized_quantity: Optional[float] = Field(None, alias="Standardized Quantity")
    standardized_price: Optional[float] = Field(None, alias="Standardized Price")
    total_transmission_charge: float = Field(..., alias="Total Transmission Charge")
    total_transaction_charge: float = Field(..., alias="Total Transaction Charge")

    @model_validator(mode="after")
    def validate_arithmetic(self) -> "TransactionData":
        # Implementation of (Price * Quantity) + Transmission = Total (+/- tolerance)
        expected = (self.price * self.transaction_quantity) + self.total_transmission_charge
        if abs(expected - self.total_transaction_charge) > (abs(self.total_transaction_charge) * 0.01 + 0.01):
             # We don't raise error here but we could. For now, just type validation.
             pass
        return self
