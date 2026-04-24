import polars as pl
from pathlib import Path
import os

from tower_kernel.config import MASTER_ROOT

class MasterDataService:
    """
    Manages global reference data (Appendix E) and lookups for the EQR Rule Engine.
    """
    
    @staticmethod
    def bootstrap_reference_data():
        """
        Initializes the master directory with core FERC reference values.
        """
        MASTER_ROOT.mkdir(parents=True, exist_ok=True)
        
        # 1. Balancing Authorities (Sample subset from Appendix E)
        ba_data = {
            "ba_code": [
                "CAISO", "PJM", "MISO", "ERCOT", "SPP", "NYISO", "ISONE", 
                "AECC", "AEC", "AESL", "AZPS", "BANC", "BPAT", "CHPD", 
                "CPBW", "CPLC", "CSWS", "DEAA", "DOPD", "DUK", "EEI", 
                "EES", "FPC", "FPL", "GCPD", "GWA", "HQT", "HST", "IID", 
                "IPCO", "ISNE", "JEA", "LDWP", "PSEI", "BCHA", "NWMT", 
                "TPWR", "HUB", "AVA", "SCL", "PACW", "PACE", "PGE", "WACM", 
                "WALC", "WAUW"
            ]
        }
        pl.DataFrame(ba_data).write_parquet(MASTER_ROOT / "balancing_authorities.parquet")
        
        # 2. Units of Measure (Appendix E)
        units_data = {
            "unit_code": [
                "$/MW", "$/MWH", "$/KW", "$/KWH", "$/KV", "cents/KWH", 
                "$/MW-DAY", "$/MW-MONTH", "$/MW-YEAR", 
                "MW", "MWH", "KW", "KWH", "KV", "FLAT RATE"
            ]
        }
        pl.DataFrame(units_data).write_parquet(MASTER_ROOT / "units_of_measure.parquet")

        # 3. Class Names
        pl.DataFrame({"code": ["F-FIRM", "N-FIRM", "NON-FIRM", "FIRM", "F", "NF"]}).write_parquet(MASTER_ROOT / "class_names.parquet")

        # 4. Term Names
        pl.DataFrame({"code": ["LONG-TERM", "SHORT-TERM", "LT", "ST"]}).write_parquet(MASTER_ROOT / "term_names.parquet")

        # 5. Increment Names
        pl.DataFrame({"code": ["HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY", "H", "D", "W", "M", "Y", "5", "15"]}).write_parquet(MASTER_ROOT / "increment_names.parquet")

        # 6. Product Types
        pl.DataFrame({"code": ["COST BASED", "MARKET BASED", "NPU", "T", "CR", "CB", "MB"]}).write_parquet(MASTER_ROOT / "product_types.parquet")

        # 7. Increment Peaking Names
        pl.DataFrame({"code": ["FP", "OP", "P", "N/A", "FULL PERIOD", "OFF-PEAK", "PEAK"]}).write_parquet(MASTER_ROOT / "peaking_names.parquet")

        # 8. Type of Rate
        pl.DataFrame({"code": ["FIXED", "FORMULA", "ELECTRIC INDEX", "RTO/ISO"]}).write_parquet(MASTER_ROOT / "rate_types.parquet")

        # 9. Time Zones
        pl.DataFrame({"code": ["AD", "AP", "AS", "CD", "CP", "CS", "ED", "EP", "ES", "MD", "MP", "MS", "PD", "PP", "PS"]}).write_parquet(MASTER_ROOT / "time_zones.parquet")

        # 10. Product Names (Core subset)
        pl.DataFrame({"code": [
            "BLACK START SERVICE", "BOOKED OUT POWER", "BUNDLED", "CAPACITY", "CUSTOMER CHARGE",
            "DIRECT ASSIGNMENT FACILITIES CHARGE", "EMERGENCY ENERGY", "ENERGY", "ENERGY IMBALANCE",
            "ENERGY IMBALANCE MARKET", "EXCHANGE", "FUEL CHARGE", "GENERATOR IMBALANCE",
            "GRANDFATHERED BUNDLED", "INTERCONNECTION AGREEMENT", "MEMBERSHIP AGREEMENT",
            "MUST RUN AGREEMENT", "NEGOTIATED-RATE TRANSMISSION", "NETWORK INTEGRATION TRANSMISSION SERVICE AGREEMENT",
            "NETWORK OPERATING AGREEMENT", "OTHER", "POINT-TO-POINT AGREEMENT", "PRIMARY FREQUENCY RESPONSE",
            "RAMPING", "REACTIVE SUPPLY & VOLTAGE CONTROL", "REAL POWER TRANSMISSION LOSS",
            "REGULATION & FREQUENCY RESPONSE", "RENEWABLE ENERGY CREDIT (REC)", "REQUIREMENTS SERVICE",
            "SCHEDULE SYSTEM CONTROL & DISPATCH", "SPINNING RESERVE", "SUPPLEMENTAL RESERVE",
            "SYSTEM OPERATING AGREEMENTS", "TOLLING ENERGY", "TRANSMISSION OWNERS AGREEMENT", "UPLIFT"
        ]}).write_parquet(MASTER_ROOT / "product_names.parquet")
        
        print(f"Master Data seeded in {MASTER_ROOT}")

    @staticmethod
    def get_lookup_set(table_name: str, column_name: str) -> set:
        """
        Loads a master table and returns a unique set of values for fast membership checks.
        """
        path = MASTER_ROOT / f"{table_name}.parquet"
        if not path.exists():
            print(f"Warning: Master lookup {table_name} not found. Bootstrapping defaults...")
            MasterDataService.bootstrap_reference_data()
            
        df = pl.read_parquet(path)
        return set(df[column_name].to_list())

if __name__ == "__main__":
    MasterDataService.bootstrap_reference_data()
