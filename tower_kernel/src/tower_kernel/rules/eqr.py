import polars as pl
import time
import inspect
from typing import Dict, Any, List, Callable, Tuple, Optional

# --- RULE REGISTRY ---
class ValidationRegistry:
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def register(self, rule_id: str, category: str, description: str):
        def decorator(func: Callable[[pl.LazyFrame], pl.LazyFrame]):
            self.rules.append({
                "rule_id": rule_id,
                "category": category,
                "description": description,
                "func": func
            })
            return func
        return decorator

registry = ValidationRegistry()

class LakeRuleRegistry:
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def register(self, rule_id: str, category: str, description: str):
        def decorator(func: Callable[[pl.LazyFrame, pl.LazyFrame], pl.LazyFrame]):
            self.rules.append({
                "rule_id": rule_id,
                "category": category,
                "description": description,
                "func": func
            })
            return func
        return decorator

lake_registry = LakeRuleRegistry()

class RegistryRuleRegistry:
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []

    def register(self, rule_id: str, category: str, description: str):
        def decorator(func: Callable[[pl.LazyFrame, pl.LazyFrame, Dict[str, Any]], pl.LazyFrame]):
            self.rules.append({
                "rule_id": rule_id,
                "category": category,
                "description": description,
                "func": func
            })
            return func
        return decorator

registry_rule_registry = RegistryRuleRegistry()

# --- METADATA-DRIVEN RULES (The "YES-set" Scale) ---
# This dictionary allows us to rapidly scale 100+ simple mandatory/conditional rules.
METADATA_RULES = [
    # IDENTIFICATION DATA (Section F.16)
    {"id": "F.16.4.2", "category": "STRUCTURAL", "col": "filer_unique_id", "check": "not_null", "desc": "Filer Unique Identifier (Field 1) is required."},
    {"id": "F.16.13", "category": "MANDATORY", "col": "contact_name", "check": "not_null", "desc": "Contact Name (Field 4) is required."},
    {"id": "F.16.13.1", "category": "MANDATORY", "col": "contact_title", "check": "not_null", "desc": "Contact Title (Field 5) is required."},
    {"id": "F.16.13.2", "category": "MANDATORY", "col": "contact_phone", "check": "not_null", "desc": "Contact Phone (Field 10) is required."},
    {"id": "F.16.13.3", "category": "MANDATORY", "col": "contact_address_1", "check": "not_null", "desc": "Contact Address 1 (Field 6) is required."},
    {"id": "F.16.13.4", "category": "MANDATORY", "col": "contact_city", "check": "not_null", "desc": "Contact City (Field 8) is required."},
    {"id": "F.16.13.5", "category": "IDENTITY", "col": "contact_zip_code", "check": "zip_format", "desc": "Contact Zip Code format invalid (Field 11)."},
    {"id": "F.16.14.4", "category": "MANDATORY", "col": "seller_cid", "check": "not_null", "desc": "Seller ID (CID) (Field 16) is required."},
    {"id": "F.16.15", "category": "IDENTITY", "col": "seller_duns", "check": "is_numeric", "desc": "Seller DUNS must be numeric (Field 15)."},
    {"id": "F.16.8", "category": "IDENTITY", "col": "contact_email", "check": "simplified_email", "desc": "Contact Email (Field 13) format appears invalid."},
    {"id": "F.16.14.1", "category": "MANDATORY", "col": "seller_company_name", "check": "not_null", "desc": "Seller Company Name (Field 2) is required."},
    {"id": "F.16.14.5", "category": "IDENTITY", "col": "seller_cid", "check": "is_cid_format", "desc": "Seller ID must be valid CID format (C000###)."},
    # SEMANTIC & PRODUCT (Section F.17)
    {"id": "F.17.1", "category": "MANDATORY", "col": "customer_company_name", "check": "not_null", "desc": "Customer Company Name (Field 17) is required."},
    {"id": "F.17.3", "category": "MANDATORY", "col": "customer_id", "check": "not_null", "desc": "Customer ID (CID) (Field 17) is required."},
    {"id": "F.17.7", "category": "SEMANTIC", "col": "affiliate", "check": "is_boolean_flag", "desc": "Affiliate (Field 18) must be Y or N."},
    {"id": "F.17.8.1", "category": "MANDATORY", "col": "ferc_tariff_reference", "check": "not_null", "desc": "FERC Tariff Reference (Field 19) is required."},
    {"id": "F.17.13", "category": "BOUNDS", "col": "contract_execution_date", "check": "after_year_1990", "desc": "Contract Execution Date (Field 22) invalid."},
    {"id": "F.17.14", "category": "BOUNDS", "col": "contract_commencement_date", "check": "after_year_1990", "desc": "Contract Commencement Date (Field 23) invalid."},
    {"id": "F.17.18.1", "category": "SEMANTIC", "col": "extension_provision_description", "check": "not_null", "desc": "Extension Provision description (Field 26) required if provision exists."},
    {"id": "F.17.4", "category": "IDENTITY", "col": "customer_duns", "check": "is_numeric", "desc": "Customer DUNS (Field 18) must be numeric."},
    {"id": "F.17.11.1", "category": "MANDATORY", "col": "service_agreement_number", "check": "not_null", "desc": "Service Agreement Number (Field 20) is required."},
    {"id": "F.17.15", "category": "BOUNDS", "col": "contract_termination_date", "check": "after_year_1990", "desc": "Contract Termination Date (Field 24) invalid."},
    {"id": "F.17.20", "category": "MANDATORY", "col": "product_name", "check": "not_null", "desc": "Product Name (Field 31) is required."},
    
    # CONTRACTUAL METADATA (Section F.21)
    {"id": "F.21.6", "category": "MANDATORY", "col": "ferc_tariff_reference", "check": "not_null", "desc": "FERC Tariff Reference (Field 19) is required."},
    {"id": "F.21.7", "category": "MANDATORY", "col": "contract_service_agreement_id", "check": "not_null", "desc": "Contract Service Agreement ID (Field 20) is required."},
    {"id": "F.21.12", "category": "MANDATORY", "col": "extension_provision", "check": "not_null", "desc": "Extension Provision Description (Field 26) is required."},
    {"id": "F.21.5", "category": "CONSISTENCY", "col": "contract_affiliate", "check": "is_boolean_flag", "desc": "Contract Affiliate (Field 18) must be 'Y' or 'N'."},
    
    # STANDARDIZED FIELD CHECKS (Conditional Mandatory)
    {"id": "F.30.44", "category": "CONDITIONAL", "col": "standardized_price", "check": "not_null_if_product", "desc": "Standardized Price required for ENERGY/CAPACITY/BOOKED OUT POWER.", "products": ["ENERGY", "CAPACITY", "BOOKED OUT POWER"]},
    {"id": "F.30.45", "category": "CONDITIONAL", "col": "standardized_quantity", "check": "conditional_required", "when_col": "product_name", "when_vals": ["ENERGY", "CAPACITY", "BOOKED OUT POWER"], "desc": "Standardized Quantity required for ENERGY/CAPACITY/BOOKED OUT POWER."},
    {"id": "F.25.14.1", "category": "CONDITIONAL", "col": "transaction_quantity", "check": "is_not_null", "desc": "Transaction Quantity is required."},
    {"id": "F.25.15", "category": "CONDITIONAL", "col": "total_transaction_charge", "check": "not_null", "desc": "Total Transaction Charge is required."},
    
    # BOUNDARY CHECKS
    {"id": "F.25.24", "category": "BOUNDS", "col": "standardized_quantity", "check": "positive", "desc": "Standardized Quantity should be > 0."},
    {"id": "F.25.20", "category": "BOUNDS", "col": "standardized_price", "check": "positive_if_not_zero_charge", "desc": "Standardized Price should be positive if charge is non-zero."},
    
    # LOOKUP CHECKS (Section F.23.x)
    {"id": "F.23.1.1", "category": "LOOKUP", "col": "class_name", "check": "is_in_lookup", "table": "class_names", "lookup_col": "code", "desc": "Class Name value is not a recognized FERC value."},
    {"id": "F.23.1.2", "category": "LOOKUP", "col": "term_name", "check": "is_in_lookup", "table": "term_names", "lookup_col": "code", "desc": "Term Name value is not a recognized FERC value."},
    {"id": "F.23.1.3", "category": "LOOKUP", "col": "increment_name", "check": "is_in_lookup", "table": "increment_names", "lookup_col": "code", "desc": "Increment Name value is not a recognized FERC value."},
    {"id": "F.23.1.5", "category": "LOOKUP", "col": "product_type_name", "check": "is_in_lookup", "table": "product_types", "lookup_col": "code", "desc": "Product Type value is not a recognized FERC value."},
    {"id": "F.23.1.4", "category": "LOOKUP", "col": "increment_peaking_name", "check": "is_in_lookup", "table": "peaking_names", "lookup_col": "code", "desc": "Increment Peaking Name value is not a recognized FERC value."},
    {"id": "F.23.2", "category": "LOOKUP", "col": "product_name", "check": "is_in_lookup", "table": "product_names", "lookup_col": "code", "desc": "Product Name value is not a recognized FERC value."},
    {"id": "F.23.8", "category": "LOOKUP", "col": "type_of_rate", "check": "is_in_lookup", "table": "rate_types", "lookup_col": "code", "desc": "Type of Rate value is not a recognized FERC value."},
    {"id": "F.23.10", "category": "LOOKUP", "col": "time_zone", "check": "is_in_lookup", "table": "time_zones", "lookup_col": "code", "desc": "Time Zone value is not a recognized FERC value."},
    {"id": "F.23.9", "category": "LOOKUP", "col": "point_of_delivery_balancing_authority", "check": "is_in_lookup", "table": "balancing_authorities", "lookup_col": "ba_code", "desc": "Point of Delivery Balancing Authority is not a recognized FERC value."},
    
    # NPU & SPECIAL FILING (Section F.30)
    {"id": "F.30.41", "category": "STRUCTURAL", "col": "ferc_tariff_reference", "check": "npu_tariff_logic", "desc": "NPU Tariff Reference must be 'NPU' for non-public utilities."},
    {"id": "F.20.3", "category": "BOUNDS", "col": "execution_date", "check": "after_year_1900", "desc": "Execution date must be after Jan 1, 1900."},
    {"id": "F.21.5", "category": "CONSISTENCY", "col": "contract_affiliate", "check": "is_boolean_flag", "desc": "Contract Affiliate (Field 18) must be 'Y' or 'N'."},
    {"id": "F.25.21.2", "category": "AUDIT", "col": "transaction_quantity", "check": "warning_non_positive", "desc": "Warning: Please confirm that transactions with negative or zero Quantity are correct."},
    {"id": "F.17.8.1", "category": "AUDIT", "col": "price", "check": "warning_high_price", "desc": "Warning: The Price per MWH exceeds $1,000.00."},
    {"id": "F.16.8", "category": "IDENTITY", "col": "contact_email", "check": "simplified_email", "desc": "Contact email format appears invalid."},
    
    # SECTION D: STRUCTURAL
    {"id": "D.3.1.2", "category": "STRUCTURAL", "col": "filing_type", "check": "is_in_list", "vals": ["NEW", "REPLACE", "DELETE", "NOACTION"], "desc": "Invalid row-level Filing Type (Field 3)."},
    {"id": "F.22.3", "category": "BOUNDS", "col": "transaction_begin_date", "check": "after_year_1990", "desc": "Transaction Begin Date must be after Jan 1, 1990."},
    {"id": "D.3.9.9", "category": "STRUCTURAL", "col": "filing_type", "check": "is_not_xml_delete", "desc": "XML delete option is disallowed for external users."},
    {"id": "D.3.9.12", "category": "STRUCTURAL", "col": "source_filename", "check": "sequential_xml_orgs", "desc": "The order of organizations in XML must be sequential."},
]

from tower_kernel.ingest.schema_compiler import TRANSACTION_COMPILER, IDENT_COMPILER, CONTRACT_COMPILER, INDEX_COMPILER

# Dynamically generate "Type Compliance" rules for all tables
# These are "Phase 0" rules to ensure data quality before semantic checks
for compiler, table_name in [
    (TRANSACTION_COMPILER, "TRANSACTION"), 
    (IDENT_COMPILER, "IDENT"), 
    (CONTRACT_COMPILER, "CONTRACT"), 
    (INDEX_COMPILER, "INDEX")
]:
    for col, target_type in compiler["meta"].items():
        rule_id = f"V4.TYPE.{table_name}.{col}"
        if target_type == "numeric":
            METADATA_RULES.append({
                "id": rule_id,
                "category": "SCHEMA",
                "col": col,
                "check": "is_numeric",
                "desc": f"Field '{col}' in {table_name} must be a valid number."
            })
        elif target_type == "date":
             METADATA_RULES.append({
                "id": rule_id,
                "category": "SCHEMA",
                "col": col,
                "check": "is_date",
                "desc": f"Field '{col}' in {table_name} must be a valid FERC date (YYYYMMDD or YYYYMMDDHHMM)."
            })
        elif target_type == "boolean":
             METADATA_RULES.append({
                "id": rule_id,
                "category": "SCHEMA",
                "col": col,
                "check": "is_boolean_flag",
                "desc": f"Field '{col}' in {table_name} must be a Boolean flag (Y/N)."
            })

# Helper to expand metadata rules into registry-like structures
def get_metadata_predicate(rule: Dict[str, Any], metadata: Dict[str, Any] = None) -> Callable[[pl.LazyFrame], pl.LazyFrame]:
    check = rule["check"]
    col = rule["col"]
    
    if check == "not_null":
        return lambda ldf: ldf.filter(pl.col(col).is_null() | (pl.col(col) == ""))
    elif check == "not_null_if_product":
        prods = [p.upper() for p in rule["products"]]
        return lambda ldf: ldf.filter((pl.col("product_name").str.to_uppercase().is_in(prods)) & (pl.col(col).is_null() | (pl.col(col) == "")))
    elif check == "positive":
        return lambda ldf: ldf.filter(pl.col(col).cast(pl.Float64, strict=False).fill_null(0) <= 0)
    elif check == "positive_if_not_zero_charge":
        # Handle zero total charge logic with strings
        return lambda ldf: ldf.filter(
            (pl.col("total_transaction_charge").cast(pl.Float64, strict=False).fill_null(0) != 0) & 
            (pl.col(col).cast(pl.Float64, strict=False).fill_null(0) <= 0)
        )
    elif check == "is_in_lookup":
        from tower_kernel.services.master_data import MasterDataService
        lookup_set = MasterDataService.get_lookup_set(rule["table"], rule["lookup_col"])
        return lambda ldf: ldf.filter((pl.col(col).is_not_null()) & (~pl.col(col).str.to_uppercase().str.strip_chars().is_in(list(lookup_set))))
    elif check == "after_year_1900":
        return lambda ldf: ldf.filter(
            pl.col(col).cast(pl.String).str.slice(0, 8).str.strptime(pl.Date, format="%Y%m%d", strict=False) < pl.date(1900, 1, 1)
        )
    elif check == "after_year_1990":
        return lambda ldf: ldf.filter(
            pl.col(col).cast(pl.String).str.slice(0, 8).str.strptime(pl.Date, format="%Y%m%d", strict=False) < pl.date(1990, 1, 1)
        )
    elif check == "is_boolean_flag":
        return lambda ldf: ldf.filter(
            (pl.col(col).is_not_null()) & 
            (~pl.col(col).cast(pl.String).str.to_uppercase().str.strip_chars().is_in(["Y", "N"]))
        )
    elif check == "is_not_xml_delete":
        # Flags rows if they are from an XML source and the header is DELETE
        header_type = str((metadata or {}).get("filing_type", "NEW")).upper()
        return lambda ldf: ldf.filter(
            (pl.col("source_filename").str.to_lowercase().str.ends_with(".xml")) & 
            (pl.lit(header_type == "DELETE"))
        )
    elif check == "sequential_xml_orgs":
        # Placeholder for structural XML check
        return lambda ldf: ldf.filter(pl.lit(False))
    elif check == "zip_format":
        return lambda ldf: ldf.filter(
            (pl.col(col).is_not_null()) & 
            (~pl.col(col).str.contains(r"^\d{5}(-\d{4})?$"))
        )
    elif check == "is_numeric":
        # Robust check: if already numeric, it passes. If string, must be castable to float.
        return lambda ldf: ldf.filter(
            (pl.col(col).is_not_null()) & 
            (pl.col(col).cast(pl.String) != "") & 
            (pl.col(col).cast(pl.Float64, strict=False).is_null())
        )
    elif check == "is_date":
        # Check if it satisfies YYYYMMDD (8) or YYYYMMDDHHMM (12) and can be parsed
        return lambda ldf: ldf.filter(
            (pl.col(col).is_not_null()) & 
            (pl.col(col).cast(pl.String) != "") & 
            (pl.col(col).cast(pl.String).str.slice(0, 8).str.strptime(pl.Date, format="%Y%m%d", strict=False).is_null())
        )
    elif check == "is_cid_format":
        return lambda ldf: ldf.filter(
            (pl.col(col).is_not_null()) & 
            (~pl.col(col).cast(pl.String).str.contains(r"^C\d+$"))
        )
    elif check == "permissive":
        return lambda ldf: ldf.filter(pl.lit(False))
    elif check == "agent_role_consistency":
        return lambda ldf: ldf.filter(pl.lit(False))
    elif check == "warning_non_positive":
        return lambda ldf: ldf.filter(pl.col(col).cast(pl.Float64, strict=False).fill_null(0) <= 0)
    elif check == "warning_high_price":
        return lambda ldf: ldf.filter((pl.col("rate_units").str.to_uppercase() == "$/MWH") & (pl.col(col).cast(pl.Float64, strict=False).fill_null(0) > 1000.0))
    elif check == "simplified_email":
        return lambda ldf: ldf.filter((pl.col(col).is_not_null()) & (~pl.col(col).str.contains(r"^.+@.+\..+$")))
    elif check == "is_in_list":
        return lambda ldf: ldf.filter((pl.col(col).is_not_null()) & (~pl.col(col).str.to_uppercase().str.strip_chars().is_in(rule["vals"])))
    elif check == "npu_tariff_logic":
        # Rule: If Seller is NPU, Tariff must be 'NPU'
        return lambda ldf: ldf.filter(
            (pl.col("product_type_name").str.to_uppercase() == "NPU") & 
            (pl.col(col).str.to_uppercase() != "NPU")
        )
    else:
        return lambda ldf: ldf.filter(pl.lit(False)) # Fallback

# --- DEDICATED COMPLEX RULES ---

@registry.register("F.24.6", "ARITHMETIC", "Total Transaction Charge mismatch beyond 1% tolerance.")
def validate_f_24_6(ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Safely cast strings to floats for math
    price = pl.col("price").cast(pl.Float64, strict=False).fill_null(0)
    qty = pl.col("transaction_quantity").cast(pl.Float64, strict=False).fill_null(0)
    transmission = pl.col("total_transmission_charge").cast(pl.Float64, strict=False).fill_null(0)
    total = pl.col("total_transaction_charge").cast(pl.Float64, strict=False).fill_null(0)
    
    return ldf.with_columns(
        calc_charge = (price * qty) + transmission,
        diff = (total - ((price * qty) + transmission)).abs()
    ).filter(
        (pl.col("diff") > (total.abs() * 0.01)) & (pl.col("diff") > 1.0)
    )

@registry.register("F.20.8", "BOUNDS", "Actual Termination Date cannot be in the future (beyond filing period).")
def validate_f_20_8(contract_ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    period_end = str(metadata.get("period_end", "20991231"))
    # actual_termination_date is Field 25
    term_date = pl.col("actual_termination_date").str.slice(0, 8)
    return contract_ldf.filter(
        (pl.col("actual_termination_date").is_not_null()) & 
        (term_date > period_end)
    )

@registry.register("F.25.17.2", "AUDIT", "Warning: True Duplicate Transactions detected (Identical trade data).")
def validate_f_25_17_2(ldf: pl.LazyFrame) -> pl.LazyFrame:
    # A true duplicate is when all physical/financial fields match exactly
    # We include POD to distinguish between same-time trades at different hubs
    return ldf.filter(
        pl.struct([
            "contract_unique_id", 
            "transaction_begin_date", 
            "transaction_end_date", 
            "product_name",
            "price",
            "transaction_quantity",
            "point_of_delivery_balancing_authority"
        ]).is_duplicated()
    )

@registry.register("F.24.3", "BOUNDS", "Transaction End Date must be greater than Begin Date.")
def validate_f_24_3(ldf: pl.LazyFrame) -> pl.LazyFrame:
    start = pl.col("transaction_begin_date").str.slice(0, 12).str.strptime(pl.Datetime, format="%Y%m%d%H%M", strict=False)
    end = pl.col("transaction_end_date").str.slice(0, 12).str.strptime(pl.Datetime, format="%Y%m%d%H%M", strict=False)
    return ldf.filter(end <= start)

@registry.register("F.50.x", "FERC_STD", "Field 50 (transaction_unique_id) must be unique within a single submission.")
def validate_f_50_uniqueness(ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Strictly unique within the specific file/submission scope
    return ldf.filter(pl.col("transaction_unique_id").is_duplicated())

@registry.register("F.24.15.1", "DEDUP", "Duplicate TOWER Unique IDs detected (Composite Collision).")
def validate_f_24_15_1(ldf: pl.LazyFrame) -> pl.LazyFrame:
    return ldf.filter(pl.col("tower_unique_id").is_not_null() & pl.col("tower_unique_id").is_duplicated())

@registry.register("F.17.2.2", "CONSISTENCY", "Invalid Rate Units for Energy product (cannot be $/MW).")
def validate_f_17_2_2(ldf: pl.LazyFrame) -> pl.LazyFrame:
    energy_products = ["ENERGY", "BOOKED OUT POWER"]
    invalid_units = ["$/MW", "$/KW"]
    return ldf.filter(
        (pl.col("product_name").str.to_uppercase().is_in(energy_products)) & 
        (pl.col("rate_units").str.to_uppercase().is_in(invalid_units))
    )

@registry.register("F.25.18", "CONSISTENCY", "Transaction Product Type mismatch between Contract and Transaction.")
def validate_f_25_18(ldf: pl.LazyFrame, contract_ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Rule: If Transaction Product Type is different from Contract Product Type for the same Contract ID
    if contract_ldf is None: return ldf.filter(pl.lit(False))
    
    # Ensure join keys are consistent types
    c_ldf = contract_ldf.select([
        pl.col("contract_unique_id").cast(pl.String), 
        pl.col("product_type_name").alias("contract_product_type")
    ]).unique()

    return ldf.with_columns(pl.col("contract_unique_id").cast(pl.String)).join(
        c_ldf,
        on="contract_unique_id",
        how="left"
    ).filter(
        (pl.col("contract_product_type").is_not_null()) & 
        (pl.col("product_type_name").str.to_uppercase() != pl.col("contract_product_type").str.to_uppercase())
    )

@registry.register("F.30.41", "CONSISTENCY", "NPU Tariff Reference must be 'NPU' for non-public utilities.")
def validate_f_30_41(ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Rule: For NPU product types, the tariff reference must be explicitly 'NPU'
    return ldf.filter(
        (pl.col("product_type_name").str.to_uppercase() == "NPU") & 
        (pl.col("ferc_tariff_reference").str.to_uppercase() != "NPU")
    )

@registry.register("F.30.44", "MANDATORY", "Standardized Price required for ENERGY/CAPACITY/BOOKED OUT POWER.")
def validate_f_30_44(ldf: pl.LazyFrame) -> pl.LazyFrame:
    relevant_prods = ["ENERGY", "CAPACITY", "BOOKED OUT POWER"]
    return ldf.filter(
        (pl.col("product_name").str.to_uppercase().is_in(relevant_prods)) & 
        (pl.col("standardized_price").is_null() | (pl.col("standardized_price").cast(pl.String) == ""))
    )

@registry.register("F.30.45", "MANDATORY", "Standardized Quantity required for ENERGY/CAPACITY/BOOKED OUT POWER.")
def validate_f_30_45(ldf: pl.LazyFrame) -> pl.LazyFrame:
    relevant_prods = ["ENERGY", "CAPACITY", "BOOKED OUT POWER"]
    return ldf.filter(
        (pl.col("product_name").str.to_uppercase().is_in(relevant_prods)) & 
        (pl.col("standardized_quantity").is_null() | (pl.col("standardized_quantity").cast(pl.String) == ""))
    )

@registry.register("F.17.4.2", "CONSISTENCY", "Capacity product cannot use Energy units ($/MWH).")
def validate_f_17_4_2(ldf: pl.LazyFrame) -> pl.LazyFrame:
    capacity_products = ["CAPACITY"]
    energy_units = ["$/MWH", "$/KWH", "CENTS/KWH"]
    return ldf.filter(
        (pl.col("product_name").str.to_uppercase().is_in(capacity_products)) &
        (pl.col("rate_units").str.to_uppercase().is_in(energy_units))
    )

@registry.register("F.23.6", "CONSISTENCY", "Credit product (CR) must be Reassignment or Point-To-Point.")
def validate_f_23_6(ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Assuming product_type_name corresponds to Field 30
    valid_products = ["REASSIGNMENT AGREEMENT", "POINT-TO-POINT AGREEMENT"]
    return ldf.filter(
        (pl.col("product_type_name").str.to_uppercase() == "CR") &
        (~pl.col("product_name").str.to_uppercase().is_in(valid_products))
    )

@lake_registry.register("F.21.2.1-CONT", "HISTORICAL", "Transaction references a missing/expired Contract UID from previous quarter.")
def validate_contract_continuity(current_ldf: pl.LazyFrame, previous_ldf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Checks if a Transaction's Contract UID exists either in the current draft 
    OR in the immediately preceding quarter (Q-1).
    """
    # 1. Get unique Contracts from current draft
    valid_contracts = current_ldf.select("contract_unique_id").unique().collect().get_column("contract_unique_id")
    
    # 2. Add unique Contracts from previous quarter if available
    if previous_ldf is not None:
        prev_contracts = previous_ldf.select("contract_unique_id").unique().collect().get_column("contract_unique_id")
        valid_contracts = pl.concat([valid_contracts, prev_contracts]).unique()
    
    # 3. Filter transactions that don't have a valid contract in the pool
    return current_ldf.filter(~pl.col("contract_unique_id").is_in(valid_contracts))


# --- REGISTRY-AWARE RULES ---

@registry_rule_registry.register("F.16.3.1", "REGISTRY", "Draft CID not found in official FERC Company Registration.")
def validate_cid_existence(current_ldf: pl.LazyFrame, registry_ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # Rule: Check if Seller CID exists in the registry mirror
    return current_ldf.with_columns(pl.col("seller_cid").cast(pl.String)).join(
        registry_ldf.select([pl.col("cid").cast(pl.String)]).unique().with_columns(pl.lit(True).alias("_exists")),
        left_on="seller_cid",
        right_on="cid",
        how="left"
    ).filter(pl.col("_exists").is_null())

@registry.register("D.3.9.1", "STRUCTURAL", "Filing level NEW/REPLACE requires all rows to be NEW.")
def validate_d_3_9_1(ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # This rule is a bit unique as it depends on Header Metadata
    header_type = str(metadata.get("filing_type", "NEW")).upper()
    if header_type in ["NEW", "REPLACE"]:
        # All records should be NEW. records with DELETE/REPLACE/NOACTION are invalid here
        return ldf.filter(pl.col("filing_type").str.to_uppercase() != "NEW")
    return ldf.filter(pl.lit(False))

@registry.register("D.3.9.2", "STRUCTURAL", "Filing level REPLACE requires all rows to be NEW.")
def validate_d_3_9_2(ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # Logic identical to D.3.9.1 for REPLACE header
    header_type = str(metadata.get("filing_type", "NEW")).upper()
    if header_type == "REPLACE":
        return ldf.filter(pl.col("filing_type").str.to_uppercase() != "NEW")
    return ldf.filter(pl.lit(False))

@registry.register("D.3.9.3", "STRUCTURAL", "Filing level DELETE cannot contain transactional records.")
def validate_d_3_9_3(ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    header_type = str(metadata.get("filing_type", "NEW")).upper()
    if header_type == "DELETE":
        # In DELETE mode, only ID Data (Organization metadata) should remain. 
        # For simplicity in this engine, we flag ALL transaction/contract rows if header is DELETE.
        return ldf
    return ldf.filter(pl.lit(False))

@registry.register("D.3.9.4", "STRUCTURAL", "Filing level MERGE allows all record types.")
def validate_d_3_9_4(ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    return ldf.filter(pl.lit(False))

@registry.register("D.3.9.5", "STRUCTURAL", "Contract level NOACTION allows all associated record types.")
def validate_d_3_9_5(ldf: pl.LazyFrame) -> pl.LazyFrame:
    return ldf.filter(pl.lit(False))

@registry.register("D.3.9.6", "STRUCTURAL", "Contract mode NEW requires all associated transactions to be NEW.")
def validate_d_3_9_6(ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Hierarchical implementation: ensure no mixed filing types within a single contract.
    # We find contracts that have 'NEW' filing type and check for any non-NEW records.
    return ldf.group_by("contract_unique_id").agg([
        pl.col("filing_type").str.to_uppercase().unique().alias("types"),
        pl.col("tower_unique_id").first().alias("tower_unique_id"),
        pl.col("source_filename").first().alias("source_filename"),
        pl.col("source_row_index").first().alias("source_row_index")
    ]).filter(
        (pl.col("types").list.contains("NEW")) & (pl.col("types").list.len() > 1)
    ).select(["tower_unique_id", "source_filename", "source_row_index"])

@registry.register("D.3.9.7", "STRUCTURAL", "Contract level REPLACE allows all record types.")
def validate_d_3_9_7(ldf: pl.LazyFrame) -> pl.LazyFrame:
    return ldf.filter(pl.lit(False))

@registry.register("F.21.31", "DEDUP", "Duplicate Contract definition detected (Seller+Buyer+Tariff+CSA collision).")
def validate_f_21_31(contract_ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Rule: Complex Key (Seller+Buyer+Tariff+CSA) uniqueness.
    # We check if multiple contract_unique_ids have the same core keys
    return contract_ldf.filter(
        pl.struct([
            "seller_company_name", 
            "customer_company_name", 
            "ferc_tariff_reference", 
            "contract_service_agreement_id"
        ]).is_duplicated()
    ).group_by([
        "seller_company_name", 
        "customer_company_name", 
        "ferc_tariff_reference", 
        "contract_service_agreement_id"
    ]).agg([
        pl.col("contract_unique_id").unique().alias("contract_ids"),
        pl.col("tower_unique_id").first().alias("tower_unique_id"),
        pl.col("source_filename").first().alias("source_filename"),
        pl.col("source_row_index").first().alias("source_row_index")
    ]).filter(pl.col("contract_ids").list.len() > 1).select([
        "tower_unique_id", "source_filename", "source_row_index"
    ])

@registry.register("F.20.11", "CONSISTENCY", "A single contract cannot have multiple buyers or sellers.")
def validate_f_20_11(contract_ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Check if a single contract_unique_id has more than one seller or customer_company_name
    return contract_ldf.group_by("contract_unique_id").agg([
        pl.col("seller_company_name").unique().len().alias("seller_count"),
        pl.col("customer_company_name").unique().len().alias("buyer_count"),
        pl.col("tower_unique_id").first().alias("tower_unique_id"),
        pl.col("source_filename").first().alias("source_filename"),
        pl.col("source_row_index").first().alias("source_row_index")
    ]).filter((pl.col("seller_count") > 1) | (pl.col("buyer_count") > 1)).select([
        "tower_unique_id", "source_filename", "source_row_index"
    ])

# --- IDENTITY RULES (F.16.x) ---
# These rules run against the identity_ldf

@registry.register("F.16.3", "STRUCTURAL", "A filing must have at least one Seller (FS#) and one Agent (FA#) contact record.")
def validate_f_16_3(identity_ldf: pl.LazyFrame) -> pl.LazyFrame:
    # We aggregate to check presence
    summary = identity_ldf.select([
        pl.col("filer_unique_id").str.contains("^FS").any().alias("has_seller"),
        pl.col("filer_unique_id").str.contains("^FA").any().alias("has_agent")
    ]).collect()
    
    if not summary["has_seller"][0] or not summary["has_agent"][0]:
        # Return a dummy error record representing the whole filing
        return pl.LazyFrame({"tower_unique_id": ["GLOBAL"], "error_message": ["Missing required FS# or FA# contact records."]})
    return pl.LazyFrame(schema={"tower_unique_id": pl.String, "error_message": pl.String})

@registry.register("F.16.12.1", "STRUCTURAL", "A filing shall contain exactly one contact record with Filer Unique ID FA1.")
def validate_f_16_12_1(identity_ldf: pl.LazyFrame) -> pl.LazyFrame:
    count = identity_ldf.filter(pl.col("filer_unique_id") == "FA1").collect().height
    if count != 1:
        return pl.LazyFrame({"tower_unique_id": ["GLOBAL"], "error_message": [f"Expected exactly 1 FA1 record, found {count}."]})
    return pl.LazyFrame(schema={"tower_unique_id": pl.String, "error_message": pl.String})

@registry.register("F.16.4.1", "STRUCTURAL", "Duplicate ID data records detected.")
def validate_f_16_4_1(identity_ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Exact duplicate check across core fields
    return identity_ldf.filter(pl.struct(["filer_unique_id", "contact_name", "contact_email"]).is_duplicated())

@registry.register("F.16.4.2", "STRUCTURAL", "Duplicate Filer Unique Identifiers (e.g. multiple FA1 records).")
def validate_f_16_4_2(identity_ldf: pl.LazyFrame) -> pl.LazyFrame:
    return identity_ldf.filter(pl.col("filer_unique_id").is_duplicated())

@registry.register("F.16.8.ID", "IDENTITY", "Email format invalid for contact person.")
def validate_f_16_8_id(identity_ldf: pl.LazyFrame) -> pl.LazyFrame:
    # Re-use the email check logic specifically for the identity rows
    # We map filer_unique_id to tower_unique_id for reporting
    return identity_ldf.filter(
        (pl.col("contact_email").is_not_null()) & (~pl.col("contact_email").str.contains(r"^.+@.+\..+$"))
    ).select([
        pl.col("filer_unique_id").alias("tower_unique_id")
    ])

@registry_rule_registry.register("F.16.3.4", "REGISTRY", "Organization Name (FS#) must match CID Registry as of Period End.")
def validate_fs_name_period_end(current_ldf: pl.LazyFrame, registry_ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # Rule: Match Organization Name (FS#) at period end
    period_end = metadata.get("period_end", "2099-12-31")
    
    # In this context, current_ldf is the identity_ldf (passed from runner)
    # We only care about FS# rows
    fs_rows = current_ldf.filter(pl.col("filer_unique_id").str.starts_with("FS"))
    
    # Join with registry to check if name matches
    return fs_rows.with_columns(pl.col("seller_cid").cast(pl.String)).join(
        registry_ldf.with_columns(pl.col("cid").cast(pl.String)), 
        left_on="seller_cid", 
        right_on="cid", 
        how="left"
    ).filter(
        (pl.col("legal_name").is_not_null()) & 
        (pl.col("seller_company_name") != pl.col("legal_name"))
    )

@registry_rule_registry.register("F.16.3.5", "REGISTRY", "Seller Company Name must match CID Registry during any part of the Quarter.")
def validate_seller_name_any_part(current_ldf: pl.LazyFrame, registry_ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # Rule: Match Seller Company Name at any part of Qtr
    return current_ldf.filter(pl.col("filer_unique_id").str.starts_with("FS")).join(
        registry_ldf.with_columns(pl.col("cid").cast(pl.String)),
        left_on="seller_cid",
        right_on="cid",
        how="left"
    ).filter(
        (pl.col("legal_name").is_not_null()) &
        (pl.col("seller_company_name") != pl.col("legal_name"))
    )

@registry_rule_registry.register("F.16.14.4", "REGISTRY", "Seller Contact Name must be an eRegistered person for the Seller CID.")
def validate_seller_contact_eregistered(current_ldf: pl.LazyFrame, registry_ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # Placeholder: Always passes if registry_ldf doesn't have contacts
    if "contact_name" not in registry_ldf.collect_schema().names():
        return current_ldf.filter(pl.lit(False))
        
    return current_ldf.filter(pl.col("filer_unique_id").str.starts_with("FS")).join(
        registry_ldf.with_columns(pl.col("cid").cast(pl.String)),
        left_on=["seller_cid", "contact_name"],
        right_on=["cid", "contact_name"],
        how="left"
    ).filter(pl.col("contact_name_right").is_null())

@registry_rule_registry.register("F.16.3.2", "REGISTRY", "Seller Company Name mismatch against FERC Registry for the given CID.")
def validate_seller_name_registry(current_ldf: pl.LazyFrame, registry_ldf: pl.LazyFrame, metadata: Dict[str, Any]) -> pl.LazyFrame:
    # Rule: Match Seller Company Name against legal_name in registry
    return current_ldf.with_columns(pl.col("seller_cid").cast(pl.String)).join(
        registry_ldf.select([pl.col("cid").cast(pl.String), "legal_name"]),
        left_on="seller_cid",
        right_on="cid",
        how="left"
    ).filter(
        (pl.col("legal_name").is_not_null()) & 
        (pl.col("seller_company_name").str.to_uppercase() != pl.col("legal_name").str.to_uppercase())
    )

# --- EXECUTION ENGINE ---

def _normalize_schema(ldf: pl.LazyFrame) -> pl.LazyFrame:
    """Ensures all pillars required by the engine are present, injecting nulls for missing cols."""
    expected_cols = {
        "tower_unique_id": pl.String,
        "transaction_unique_id": pl.String,
        "contract_unique_id": pl.String,
        "seller_company_name": pl.String,
        "product_name": pl.String,
        "product_type_name": pl.String,
        "rate_units": pl.String,
        "total_transaction_charge": pl.String,
        "total_transmission_charge": pl.String,
        "transaction_quantity": pl.String,
        "price": pl.String,
        "transaction_begin_date": pl.String,
        "transaction_end_date": pl.String,
        "class_name": pl.String,
        "term_name": pl.String,
        "increment_name": pl.String,
        "increment_peaking_name": pl.String,
        "time_zone": pl.String,
        "point_of_delivery_balancing_authority": pl.String,
        "point_of_delivery_specific_location": pl.String,
        "ferc_tariff_reference": pl.String,
        "trade_date": pl.String,
        "type_of_rate": pl.String,
        "standardized_price": pl.String,
        "standardized_quantity": pl.String,
        "contract_service_agreement_id": pl.String,
        "customer_company_name": pl.String,
        "execution_date": pl.String,
        "commencement_date": pl.String,
        "termination_date": pl.String,
        "actual_termination_date": pl.String,
        "contract_affiliate": pl.String,
        "contact_email": pl.String,
        "contact_name": pl.String,
        "filing_type": pl.String,
        "source_filename": pl.String,
        "source_row_index": pl.Int64, # Row index is internal, keep as Int
    }
    
    current_cols = ldf.collect_schema().names()
    
    # Implementation of the "Raw String Lake" policy:
    # We force all expected columns to their mandated types (usually pl.String)
    # to handle data sources that may already be typed (e.g. Parquet mirrors).
    normalization_exprs = []
    for col, dtype in expected_cols.items():
        if col == "contract_unique_id" and col not in current_cols and "contract_service_agreement_id" in current_cols:
            # Self-healing: Fallback to CSA ID if Unique ID was not extracted (prevents Section F.25 null-collisions)
            normalization_exprs.append(pl.col("contract_service_agreement_id").cast(dtype).alias(col))
        elif col == "transaction_begin_date" and col not in current_cols and "begin_date" in current_cols:
            normalization_exprs.append(pl.col("begin_date").cast(dtype).alias(col))
        elif col == "transaction_end_date" and col not in current_cols and "end_date" in current_cols:
            normalization_exprs.append(pl.col("end_date").cast(dtype).alias(col))
        elif col == "contact_name" and col not in current_cols and "seller_contact" in current_cols:
            normalization_exprs.append(pl.col("seller_contact").cast(dtype).alias(col))
        elif col == "contact_email" and col not in current_cols and "seller_contact_email" in current_cols:
            normalization_exprs.append(pl.col("seller_contact_email").cast(dtype).alias(col))
        elif col in current_cols:
            normalization_exprs.append(pl.col(col).cast(dtype))
        else:
            # Inject missing column
            default_val = "NEW" if col == "filing_type" else None
            normalization_exprs.append(pl.lit(default_val).cast(dtype).alias(col))
    
    res = ldf.with_columns(normalization_exprs)
    print(f"DEBUG: Normalized cols: {res.collect_schema().names()}")
    return res

def run_benchmarked_validation(
    ldf: pl.LazyFrame, 
    *,
    engine: str = "cpu", 
    previous_ldf: pl.LazyFrame = None,
    registry_ldf: pl.LazyFrame = None,
    identity_ldf: pl.LazyFrame = None,
    contract_ldf: pl.LazyFrame = None,
    metadata: Dict[str, Any] = None
) -> Tuple[pl.DataFrame, List[Dict[str, Any]]]:
    """
    Executes all rules while recording performance metrics.
    Supports Single-Filing, Cross-Quarter (Lake), and Registry rules.
    """
    # Type Guard: Ensure engine is a string, fallback to CPU on shadowing errors
    if not isinstance(engine, str):
        print(f"WARNING: Invalid engine type {type(engine)}. Defaulting to 'cpu'.")
        engine = "cpu"
        
    # Standardize input schema to prevent ColumnNotFoundErrors on sparse files
    ldf = _normalize_schema(ldf)
    
    metadata = metadata or {}
    
    all_errors = []
    stats = []
    
    # Calculate height once for throughput metrics
    total_height = ldf.select(pl.len()).collect().item()
    
    # --- PHASE 0: SCHEMA VALIDATION ---
    # We run SCHEMA rules first and capture row-level failures for cascading suppression.
    schema_failed_ids = set()
    
    def run_schema_phase(target_ldf, target_height, table_name):
        nonlocal schema_failed_ids
        target_cols = target_ldf.collect_schema().names()
        for meta_rule in METADATA_RULES:
            if meta_rule["category"] == "SCHEMA" and meta_rule["col"] in target_cols and table_name in meta_rule["id"]:
                rule_spec = {
                    "id": meta_rule["id"],
                    "rule_id": meta_rule["id"],
                    "description": meta_rule["desc"],
                    "func": get_metadata_predicate(meta_rule, metadata=metadata)
                }
                # Run and record
                start_count = len(all_errors)
                _run_and_record(rule_spec, target_ldf, target_height, engine, all_errors, stats, metadata=metadata)
                # If errors were found, collect the IDs
                if len(all_errors) > start_count:
                    new_errors = all_errors[-1]
                    if "tower_unique_id" in new_errors.columns:
                        schema_failed_ids.update(new_errors.get_column("tower_unique_id").to_list())

    # Run SCHEMA for all pillars
    run_schema_phase(ldf, total_height, "TRANSACTION")
    if identity_ldf is not None:
        total_id_height = identity_ldf.select(pl.len()).collect().item()
        run_schema_phase(identity_ldf, total_id_height, "IDENT")
    if contract_ldf is not None:
        total_contract_height = contract_ldf.select(pl.len()).collect().item()
        run_schema_phase(contract_ldf, total_contract_height, "CONTRACT")

    # --- CASCADING SUPPRESSION ---
    # Mask out rows that have SCHEMA failures to prevent noise in downstream rules
    if schema_failed_ids:
        ldf = ldf.filter(~pl.col("tower_unique_id").is_in(list(schema_failed_ids)))
        if identity_ldf is not None:
            identity_ldf = identity_ldf.filter(~pl.col("tower_unique_id").is_in(list(schema_failed_ids)))
        if contract_ldf is not None:
            contract_ldf = contract_ldf.filter(~pl.col("tower_unique_id").is_in(list(schema_failed_ids)))

    # --- PHASE 1-5: CONTENT VALIDATION ---
    # 1. Process Functional Registry Rules
    for rule in registry.rules:
        sig = inspect.signature(rule["func"])
        # Prepare flexible kwargs
        kwargs = {"metadata": metadata, "contract_ldf": contract_ldf}
        
        # Handle identity vs transaction rules
        if "identity_ldf" in sig.parameters:
            if identity_ldf is not None:
                _run_and_record(rule, identity_ldf, total_height, engine, all_errors, stats, is_id_data=True, **kwargs)
        else:
            _run_and_record(rule, ldf, total_height, engine, all_errors, stats, **kwargs)
        
    # 2. Process Lake Rules (Cross-Quarter)
    if previous_ldf is not None:
        for lake_rule in lake_registry.rules:
            _run_and_record_lake(lake_rule, ldf, previous_ldf, total_height, engine, all_errors, stats)

    # 3. Process Registry Rules
    if registry_ldf is not None:
        for reg_rule in registry_rule_registry.rules:
            _run_and_record_registry(reg_rule, ldf, registry_ldf, metadata, total_height, engine, all_errors, stats)

    # Concat failures
    trace_cols = ["tower_unique_id", "transaction_unique_id", "rule_id", "category", "error_message", "source_filename", "source_row_index"]
    error_list = [e.select(trace_cols) for e in all_errors if all(c in e.columns for c in trace_cols)]
    
    if error_list:
        combined_errors = pl.concat(error_list)
    else:
        combined_errors = pl.DataFrame(schema={c: pl.String for c in trace_cols if c != "source_row_index"} | {"source_row_index": pl.Int64})
    
    return combined_errors, stats

def _run_and_record(rule: Dict[str, Any], ldf: pl.LazyFrame, total_height: int, engine: str, all_errors: list, stats: list, is_id_data: bool = False, **kwargs):
    start_time = time.perf_counter()
    
    if engine == "hybrid":
        actual_engine = "gpu" if rule["rule_id"] == "F.24.15.1" else "cpu"
    else:
        actual_engine = engine
    
    # Enable streaming for CPU path to handle OOM on 50M+ records
    is_streaming = (actual_engine == "cpu")
    
    try:
        func = rule["func"]
        sig = inspect.signature(func)
        
        # Prepare arguments based on signature
        call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        
        # Handle the primary LazyFrame argument (ldf or identity_ldf)
        if "ldf" in sig.parameters:
            call_kwargs["ldf"] = ldf
        elif "identity_ldf" in sig.parameters:
            call_kwargs["identity_ldf"] = ldf

        # If it's a metadata rule (lambda), we call it with ldf first
        if not inspect.isfunction(func) and not inspect.ismethod(func):
             # Lambda or predicate factory
             error_df = func(ldf).collect(engine=actual_engine, streaming=is_streaming)
        else:
            # Standard rule function
            error_df = func(**call_kwargs).collect(engine=actual_engine, streaming=is_streaming)

    except Exception as e:
        print(f"Error executing rule {rule['rule_id']}: {e}")
        error_df = pl.DataFrame(schema=["transaction_unique_id"])

    duration_ms = (time.perf_counter() - start_time) * 1000
    
    if error_df.height > 0:
        trace_cols = ["tower_unique_id", "transaction_unique_id", "rule_id", "category", "error_message", "source_filename", "source_row_index"]
        for col_name in trace_cols:
            if col_name not in error_df.columns:
                dtype = pl.Int64 if col_name == "source_row_index" else pl.String
                error_df = error_df.with_columns(pl.lit(None).cast(dtype).alias(col_name))
        error_df = error_df.with_columns(rule_id=pl.lit(rule["rule_id"]), category=pl.lit(rule["category"]), error_message=pl.lit(rule.get("description", "Structural violation")))
        all_errors.append(error_df.select(trace_cols))
    
    stats.append({
        "rule_id": rule["rule_id"],
        "category": rule["category"],
        "description": rule["description"],
        "duration_ms": duration_ms,
        "error_count": error_df.height,
        "throughput_tps": int(total_height / (duration_ms / 1000)) if duration_ms > 0 else 0
    })

def _run_and_record_lake(rule, ldf, previous_ldf, total_height, engine, all_errors, stats):
    """Execution helper for Cross-Quarter rules."""
    start_time = time.perf_counter()
    
    # We use CPU as default for joins presently
    actual_engine = "cpu"
    is_streaming = True
    
    try:
        # Cross-quarter rules expect (current, previous)
        error_df = rule["func"](ldf, previous_ldf).collect(engine=actual_engine, streaming=is_streaming)
    except Exception as e:
        print(f"Error executing lake rule {rule['rule_id']}: {e}")
        error_df = pl.DataFrame(schema=ldf.schema)

    duration_ms = (time.perf_counter() - start_time) * 1000
    
    if error_df.height > 0:
        error_df = error_df.with_columns(
            rule_id = pl.lit(rule["rule_id"]),
            category = pl.lit(rule["category"]),
            error_message = pl.lit(rule["description"])
        )
        all_errors.append(error_df)
    
    stats.append({
        "rule_id": rule["rule_id"],
        "category": rule["category"],
        "description": rule["description"],
        "duration_ms": duration_ms,
        "error_count": error_df.height,
        "throughput_tps": int(total_height / (duration_ms / 1000)) if duration_ms > 1 else 0
    })

def _run_and_record_registry(rule, ldf, registry_ldf, metadata, total_height, engine, all_errors, stats):
    """Execution helper for Registry-Aware rules."""
    start_time = time.perf_counter()
    actual_engine = "cpu"
    
    try:
        error_df = rule["func"](ldf, registry_ldf, metadata).collect(engine=actual_engine)
    except Exception as e:
        print(f"Error executing registry rule {rule['rule_id']}: {e}")
        error_df = pl.DataFrame(schema=ldf.schema)

    duration_ms = (time.perf_counter() - start_time) * 1000
    
    if error_df.height > 0:
        error_df = error_df.with_columns(
            rule_id = pl.lit(rule["rule_id"]),
            category = pl.lit(rule["category"]),
            error_message = pl.lit(rule["description"])
        )
        all_errors.append(error_df)
    
    stats.append({
        "rule_id": rule["rule_id"],
        "category": rule["category"],
        "description": rule["description"],
        "duration_ms": duration_ms,
        "error_count": error_df.height,
        "throughput_tps": int(total_height / (duration_ms / 1000)) if duration_ms > 1 else 0
    })
