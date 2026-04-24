import polars as pl
from typing import Dict, Any, Type, List
from pydantic import BaseModel
from tower_kernel.model_v40 import IdentificationData, ContractData, TransactionData, IndexData

class SchemaCompiler:
    """
    Bridges Pydantic v4.0 Models to Polars Schemas for the 'Bronze Lake' paradigm.
    Extracts FERC Aliases (CSV headers) and maps them to internal snake_case properties.
    Ensures all ingestion columns are treated as Strings to preserve raw user input.
    """

    @classmethod
    def get_bronze_schema(cls, model: Type[BaseModel]) -> pl.Schema:
        """
        Returns a Polars schema where every field in the Pydantic model 
        (sourced via its alias) is mapped to pl.String.
        """
        # We iterate over model_fields (Pydantic v2)
        # We want the keys to be the ALIASES (FERC Title Case) as they appear in the CSV
        schema_dict = {}
        for field_name, field_info in model.model_fields.items():
            alias = field_info.alias or field_name
            schema_dict[alias] = pl.String
            
        return pl.Schema(schema_dict)

    @classmethod
    def get_rename_map(cls, model: Type[BaseModel]) -> Dict[str, str]:
        """
        Returns a mapping of {Alias: FieldName} for exact matches.
        """
        rename_map = {}
        for field_name, field_info in model.model_fields.items():
            alias = field_info.alias or field_name
            if alias != field_name:
                rename_map[alias] = field_name
        return rename_map

    @classmethod
    def get_robust_rename_map(cls, model: Type[BaseModel], actual_columns: List[str]) -> Dict[str, str]:
        """
        Performs Case-Insensitive, Space-Insensitive, and Underscore-Insensitive 
        matching between raw CSV headers and Pydantic model aliases.
        Also handles cases where "ID" or "Identifier" suffixes are present or missing.
        """
        def normalize(s: str) -> str:
            val = s.lower().replace(" ", "").replace("_", "").strip()
            # aggressive stripping of common identifiers to maximize matching
            if val.endswith("id"): val = val[:-2]
            if val.endswith("identifier"): val = val[:-10]
            return val

        # Map {NormalizedBasis: FinalFieldName}
        norm_map = {}
        for field_name, field_info in model.model_fields.items():
            alias = field_info.alias or field_name
            norm_map[normalize(alias)] = field_name
            norm_map[normalize(field_name)] = field_name

        rename_map = {}
        used_targets = set()
        
        # Priority 1: Exact matches (case-insensitive) shouldn't be overridden by fuzzy matches
        for col in actual_columns:
            lcol = col.lower()
            for field_name, field_info in model.model_fields.items():
                alias = (field_info.alias or field_name).lower()
                if lcol == alias or lcol == field_name.lower():
                    if field_name not in used_targets:
                        if field_name != col:
                            rename_map[col] = field_name
                        used_targets.add(field_name)
                        break

        # Priority 2: Fuzzy matches for remaining columns
        for col in actual_columns:
            if col in rename_map or col in used_targets: continue
            
            norm_col = normalize(col)
            if norm_col in norm_map:
                target_field = norm_map[norm_col]
                if target_field not in used_targets:
                    if target_field != col:
                        rename_map[col] = target_field
                    used_targets.add(target_field)
        
        return rename_map

    @classmethod
    def get_target_metadata(cls, model: Type[BaseModel]) -> Dict[str, str]:
        """
        Returns metadata about the 'intended' types for the fields, 
        allowing the validation engine to know which fields should be cast to 
        Numerical or Date types.
        """
        metadata = {}
        for field_name, field_info in model.model_fields.items():
            # Basic heuristic for type detection from Pydantic field annotation or name
            ann = str(field_info.annotation).lower()
            lower_name = field_name.lower()
            if "float" in ann or "int" in ann:
                metadata[field_name] = "numeric"
            elif "date" in ann or "datetime" in ann or "date" in lower_name:
                metadata[field_name] = "date"
            else:
                metadata[field_name] = "string"
        return metadata

# Exported singletons for easy access
IDENT_COMPILER = {
    "model": IdentificationData,
    "schema": SchemaCompiler.get_bronze_schema(IdentificationData),
    "rename": SchemaCompiler.get_rename_map(IdentificationData),
    "meta": SchemaCompiler.get_target_metadata(IdentificationData)
}

CONTRACT_COMPILER = {
    "model": ContractData,
    "schema": SchemaCompiler.get_bronze_schema(ContractData),
    "rename": SchemaCompiler.get_rename_map(ContractData),
    "meta": SchemaCompiler.get_target_metadata(ContractData)
}

TRANSACTION_COMPILER = {
    "model": TransactionData,
    "schema": SchemaCompiler.get_bronze_schema(TransactionData),
    "rename": SchemaCompiler.get_rename_map(TransactionData),
    "meta": SchemaCompiler.get_target_metadata(TransactionData)
}

INDEX_COMPILER = {
    "model": IndexData,
    "schema": SchemaCompiler.get_bronze_schema(IndexData),
    "rename": SchemaCompiler.get_rename_map(IndexData),
    "meta": SchemaCompiler.get_target_metadata(IndexData)
}
