from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

class Seller(BaseModel):
    """Root dimension for entity identification."""
    seller_company_id_ferc: str = Field(..., description="Primary Key")
    seller_company_name: str

class Contract(BaseModel):
    """Metadata for service agreements."""
    global_contract_id: str = Field(..., description="Primary Key")
    seller_company_id_ferc: str = Field(..., description="Foreign Key -> Seller")
    contract_unique_id: str
    customer_company_name: str
    year_quarter: str = Field(..., description="Partitioning column")
    contract_affiliate: bool
    ferc_tariff_reference: Optional[str] = None
    contract_execution_date: date
    commencement_date_of_contract_term: date
    contract_termination_date: Optional[date] = None

class ContractTerm(BaseModel):
    """Granular terms defined within a contract."""
    term_id: str = Field(..., description="Primary Key")
    global_contract_id: str = Field(..., description="Foreign Key -> Contract")
    product_name: str
    product_type_name: str
    quantity: float
    units: str
    rate: float
    begin_date: datetime
    end_date: datetime

class Transaction(BaseModel):
    """High-volume fact table. Optimized for massive scans."""
    transaction_unique_id: str = Field(..., description="Filing-scoped Unique ID")
    contract_service_agreement_id: str = Field(..., description="Field 20")
    seller_transaction_id: str = Field(..., description="Field 50")
    transaction_begin_date: datetime = Field(..., description="Field 51")
    transaction_end_date: datetime = Field(..., description="Field 52")
    trade_date: Optional[date] = Field(None, description="Field 53")
    product_name: str = Field(..., description="Field 63")
    transaction_quantity: float = Field(..., description="Field 64")
    price: float = Field(..., description="Field 65")
    rate_units: str = Field(..., description="Field 66")
    standardized_quantity: Optional[float] = Field(None, description="Field 67")
    standardized_price: Optional[float] = Field(None, description="Field 68")
    total_transmission_charge: float = Field(default=0.0, description="Field 69")
    total_transaction_charge: float = Field(..., description="Field 70")
    ingestion_timestamp: datetime = Field(default_factory=datetime.now)
    source_filename: Optional[str] = None
    source_row_index: Optional[int] = None
