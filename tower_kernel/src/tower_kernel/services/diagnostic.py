import polars as pl
import os
import datetime
import pyarrow.parquet as pq
from pathlib import Path
from tower_kernel.rules.eqr import run_benchmarked_validation, registry, lake_registry, registry_rule_registry, METADATA_RULES, get_metadata_predicate, _normalize_schema
from tower_kernel.services.audit_agent import RegulatoryAuditorAgent
from tower_kernel.services.registry_mirror import RegistryMirrorService
import tower_kernel.config as config
import shutil

REPORT_BASE = "data/reports"

class DiagnosticService:
    @staticmethod
    def get_compliance_scorecard(workspace_parquet_path: str):
        """
        Runs full validation on a draft workspace and returns a high-level scorecard.
        Includes Cross-Quarter checks by discovering the filer's previous quarter and history.
        """
        ldf = pl.scan_parquet(workspace_parquet_path)
        
        # 1. Discover Historical Context (Q-1)
        previous_ldf = DiagnosticService._discover_previous_quarter(workspace_parquet_path)
        
        # 2. Get Registry Mirror Context (Ensuring daily sync)
        RegistryMirrorService.ensure_synced()
        registry_ldf = RegistryMirrorService.get_mirror_ldf()
        
        # 3. Extract metadata and identity context
        meta = pq.read_metadata(workspace_parquet_path).metadata
        meta_dict = {k.decode("utf-8"): v.decode("utf-8") if isinstance(v, bytes) else v for k, v in meta.items()} if meta else {}
        
        identity_path = Path(workspace_parquet_path).parent / "identity.parquet"
        identity_ldf = pl.scan_parquet(identity_path) if identity_path.exists() else None
        
        contract_path = Path(workspace_parquet_path).parent / "contract.parquet"
        contract_ldf = pl.scan_parquet(contract_path) if contract_path.exists() else None
        
        # 4. Execute the kernel validation engine
        errors_df, stats = run_benchmarked_validation(
            ldf, 
            engine="cpu", 
            previous_ldf=previous_ldf,
            registry_ldf=registry_ldf,
            identity_ldf=identity_ldf,
            contract_ldf=contract_ldf,
            metadata=meta_dict
        )
        
        total_records = ldf.select(pl.len()).collect().item()
        
        # 5. Aggregation logic for the 5-TYPE TOWER Ontology
        categories = {
            "Type 1: Foundational": {"fails": 0, "total": 0, "desc": "Value format & Data type", "rules": []},
            "Type 2: DD Foundations": {"fails": 0, "total": 0, "desc": "Intra-record field value", "rules": []},
            "Type 3: XULE Logic":     {"fails": 0, "total": 0, "desc": "Intra-record cross-field", "rules": []},
            "Type 4: Cross-Quarter":  {"fails": 0, "total": 0, "desc": "Field values across quarters", "rules": []},
            "Type 5: Forensic":       {"fails": 0, "total": 0, "desc": "Cross-record & outlier detection", "rules": []}
        }
        
        category_map = {
            "SCHEMA":     "Type 1: Foundational",
            "STRUCTURAL": "Type 1: Foundational",
            "MANDATORY":  "Type 2: DD Foundations", 
            "LOOKUP":     "Type 2: DD Foundations",
            "IDENTITY":   "Type 2: DD Foundations",
            "ARITHMETIC": "Type 3: XULE Logic", 
            "CONSISTENCY": "Type 3: XULE Logic", 
            "CONDITIONAL": "Type 3: XULE Logic",
            "DEDUP":       "Type 3: XULE Logic",
            "HISTORICAL": "Type 4: Cross-Quarter",
            "BOUNDS":     "Type 5: Forensic",
            "AUDIT":      "Type 5: Forensic",
            "REGISTRY":   "Type 2: DD Foundations"
        }
        
        # 6. Aggregate stats
        rule_scorecard = {}
        for s in stats:
            cat_name = category_map.get(s["category"], "Type 5: Forensic")
            categories[cat_name]["fails"] += s["error_count"]
            categories[cat_name]["total"] += total_records 
            
            # Add rule detail to the category
            categories[cat_name]["rules"].append({
                "id": s["rule_id"],
                "fails": s["error_count"],
                "total": total_records,
                "desc": s["description"]
            })
            
            rule_scorecard[s["rule_id"]] = {
                "fails": s["error_count"],
                "total": total_records,
                "category": s["category"]
            }
            
        return {
            "total_records": total_records,
            "scorecard": rule_scorecard,
            "categories": categories,
            "timestamp": datetime.datetime.now(),
            "has_historical_context": previous_ldf is not None,
            "promoted_to_silver": False
        }


    @staticmethod
    def _discover_previous_quarter(draft_path: str):
        """
        Internal helper to find the Q-1 partition for the current filer.
        Uses Metadata Branding to ensure identity match.
        """
        try:
            # Extract metadata from the draft branding
            meta = pq.read_metadata(draft_path).metadata
            if not meta: return None
            
            company_id = meta.get(b"company_id", b"").decode("utf-8")
            year = int(meta.get(b"year", 0))
            quarter = int(meta.get(b"quarter", 0))
            
            if not company_id or not year or not quarter:
                return None
            
            # Search Gold Lake first for authoritative history, fallback to Silver
            for tier in [config.TIER_GOLD, config.TIER_SILVER]:
                tier_path = config.get_tier_path(company_id, tier)
                tx_path = tier_path / config.TABLE_TRANSACTIONS
                
                if tx_path.exists():
                    # Check if the data in this consolidated lake actually contains our target slice
                    # In Gen 3, Gold is consolidated. We filter by year/quarter.
                    ldf = pl.scan_parquet(tx_path)
                    slice_ldf = ldf.filter((pl.col("filing_year") == str(prev_year)) & (pl.col("filing_quarter") == str(prev_quarter)))
                    
                    if slice_ldf.select(pl.len()).collect().item() > 0:
                        print(f"Historical Context Found in {tier} Tier for {company_id} {prev_year}Q{prev_quarter}")
                        return slice_ldf

            return None
        except Exception as e:
            print(f"Warning: Could not discover historical context: {e}")
            return None

    @staticmethod
    def get_rule_evidence(workspace_parquet_path: str, rule_id: str, limit: int = 100):
        """
        Drill-down function for the TOWER-C UI. 
        Returns specific records that violated a given rule.
        """
        # 1. Identity the rule function from all registries
        rule = next((r for r in registry.rules if r["rule_id"] == rule_id), None)
        registry_type = "functional"
        meta_rule = None
        
        if not rule:
            rule = next((r for r in lake_registry.rules if r["rule_id"] == rule_id), None)
            registry_type = "lake"
            
        if not rule:
            rule = next((r for r in registry_rule_registry.rules if r["rule_id"] == rule_id), None)
            registry_type = "registry"
            
        if not rule:
            meta_rule = next((r for r in METADATA_RULES if r["id"] == rule_id), None)
            if meta_rule:
                rule = {
                    "rule_id": meta_rule["id"],
                    "func": get_metadata_predicate(meta_rule)
                }
                registry_type = "functional"
        
        if not rule:
            print(f"Error: Rule {rule_id} not found.")
            return None
            
        # 2. Resolve Target Table (Transactions vs Ident vs Contracts)
        base_dir = Path(workspace_parquet_path).parent
        target_file = Path(workspace_parquet_path).name
        
        if (registry_type == "registry" and rule_id.startswith("F.16")) or \
           (rule_id.startswith("F.16")) or \
           (meta_rule and "IDENT" in rule_id) or \
           (meta_rule and meta_rule.get("table") == "ident"):
            target_file = config.TABLE_IDENT
        elif (rule_id.startswith("F.20")) or \
             (rule_id.startswith("F.21")) or \
             (meta_rule and "CONTRACT" in rule_id) or \
             (meta_rule and meta_rule.get("table") == "contracts"):
            target_file = config.TABLE_CONTRACTS
            
        target_path = base_dir / target_file
        if not target_path.exists():
            target_path = Path(workspace_parquet_path) # Fallback
            
        ldf = pl.scan_parquet(target_path)
        ldf = _normalize_schema(ldf)
        
        # 2. Resolve dependencies for complex rules
        registry_ldf = None
        previous_ldf = None
        metadata = {}
        identity_ldf = None
        contract_ldf = None
        
        import inspect
        sig = inspect.signature(rule["func"]) if callable(rule["func"]) else None
        if sig:
            if "contract_ldf" in sig.parameters:
                c_path = base_dir / config.TABLE_CONTRACTS
                if c_path.exists():
                    contract_ldf = _normalize_schema(pl.scan_parquet(c_path))
            if "identity_ldf" in sig.parameters:
                i_path = base_dir / config.TABLE_IDENT
                if i_path.exists():
                    identity_ldf = _normalize_schema(pl.scan_parquet(i_path))

        
        # Peek at metadata for context (Required for F.20.8, etc.)
        meta = pq.read_metadata(workspace_parquet_path).metadata
        metadata = {k.decode("utf-8"): v.decode("utf-8") if isinstance(v, bytes) else v for k, v in meta.items()} if meta else {}

        if registry_type == "lake":
            previous_ldf = DiagnosticService._discover_previous_quarter(workspace_parquet_path)
        if registry_type == "registry":
            RegistryMirrorService.ensure_synced()
            registry_ldf = RegistryMirrorService.get_mirror_ldf()

        # 3. Execute with appropriate context
        try:
            if registry_type == "functional":
                if sig:
                    call_kwargs = {}
                    if "ldf" in sig.parameters: call_kwargs["ldf"] = ldf
                    if "identity_ldf" in sig.parameters and identity_ldf is not None: call_kwargs["identity_ldf"] = identity_ldf
                    if "contract_ldf" in sig.parameters and contract_ldf is not None: call_kwargs["contract_ldf"] = contract_ldf
                    if "metadata" in sig.parameters: call_kwargs["metadata"] = metadata
                    evidence_ldf = rule["func"](**call_kwargs)
                else:
                    evidence_ldf = rule["func"](ldf)
            elif registry_type == "lake":
                evidence_ldf = rule["func"](ldf, previous_ldf)
            elif registry_type == "registry":
                evidence_ldf = rule["func"](ldf, registry_ldf, metadata)
            else:
                return None
                
            evidence_df = evidence_ldf.head(limit).collect()
            return evidence_df
        except Exception as e:
            print(f"Error executing evidence fetch for {rule_id}: {e}")
            raise e

    @staticmethod
    def export_compliance_report(workspace_parquet_path: str, filer_id: str, format: str = "parquet"):
        """
        Persists the validation results to the Artifact Store for internal auditing.
        """
        ldf = pl.scan_parquet(workspace_parquet_path)
        errors_df, _ = run_benchmarked_validation(ldf, engine="cpu")
        
        # Use CID-relative Reports tier
        report_dir = config.get_tier_path(filer_id, config.TIER_REPORTS)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"compliance_summary_{timestamp}.{format}"
        
        if format == "parquet":
            errors_df.write_parquet(report_path)
        elif format == "csv":
            errors_df.write_csv(report_path)
            
        print(f"Compliance report exported to: {report_path}")
        return str(report_path)

    @staticmethod
    def analyze_failure_set_with_ai(workspace_parquet_path: str, rule_id: str):
        """
        Targeted AI Analysis for a specific failure record set.
        Uses Cluster Sampling to give the AI context on the 'types' of errors.
        """
        # 1. Identity the rule metadata and function from all registries
        rule_meta = next((r for r in registry.rules if r["rule_id"] == rule_id), None)
        registry_type = "functional"
        meta_rule = None
        
        if not rule_meta:
            rule_meta = next((r for r in lake_registry.rules if r["rule_id"] == rule_id), None)
            registry_type = "lake"
            
        if not rule_meta:
            rule_meta = next((r for r in registry_rule_registry.rules if r["rule_id"] == rule_id), None)
            registry_type = "registry"
            
        if not rule_meta:
            meta_rule = next((r for r in METADATA_RULES if r["id"] == rule_id), None)
            if meta_rule:
                rule_meta = {
                    "rule_id": meta_rule["id"],
                    "func": get_metadata_predicate(meta_rule),
                    "description": meta_rule.get("desc", "No description")
                }
                registry_type = "functional"
        
        if not rule_meta:
            return {"error": "Rule not found"}
            
        # 2. Resolve Target Table
        base_dir = Path(workspace_parquet_path).parent
        target_file = Path(workspace_parquet_path).name
        
        if (registry_type == "registry" and rule_id.startswith("F.16")) or \
           (meta_rule and "IDENT" in rule_id) or \
           (meta_rule and meta_rule.get("table") == "ident"):
            target_file = config.TABLE_IDENT
        elif (meta_rule and "CONTRACT" in rule_id) or \
             (meta_rule and meta_rule.get("table") == "contracts"):
            target_file = config.TABLE_CONTRACTS
            
        target_path = base_dir / target_file
        if not target_path.exists():
            target_path = Path(workspace_parquet_path) # Fallback
            
        ldf = pl.scan_parquet(target_path)
        ldf = _normalize_schema(ldf)

        # 2. Resolve dependencies for complex rules
        registry_ldf = None
        previous_ldf = None
        metadata = {}
        identity_ldf = None
        contract_ldf = None
        
        import inspect
        sig = inspect.signature(rule_meta["func"]) if callable(rule_meta["func"]) else None
        if sig:
            if "contract_ldf" in sig.parameters:
                c_path = base_dir / config.TABLE_CONTRACTS
                if c_path.exists():
                    contract_ldf = _normalize_schema(pl.scan_parquet(c_path))
            if "identity_ldf" in sig.parameters:
                i_path = base_dir / config.TABLE_IDENT
                if i_path.exists():
                    identity_ldf = _normalize_schema(pl.scan_parquet(i_path))
        
        if registry_type in ["lake", "registry"] or rule_id.startswith("D.3.9"):
            meta = pq.read_metadata(workspace_parquet_path).metadata
            metadata = {k.decode("utf-8"): v.decode("utf-8") if isinstance(v, bytes) else v for k, v in meta.items()} if meta else {}
            
            if registry_type == "lake":
                previous_ldf = DiagnosticService._discover_previous_quarter(workspace_parquet_path)
            if registry_type == "registry":
                RegistryMirrorService.ensure_synced()
                registry_ldf = RegistryMirrorService.get_mirror_ldf()

        # 3. Filter for failing records
        try:
            if registry_type == "functional":
                if sig:
                    call_kwargs = {}
                    if "ldf" in sig.parameters: call_kwargs["ldf"] = ldf
                    if "identity_ldf" in sig.parameters and identity_ldf is not None: call_kwargs["identity_ldf"] = identity_ldf
                    if "contract_ldf" in sig.parameters and contract_ldf is not None: call_kwargs["contract_ldf"] = contract_ldf
                    if "metadata" in sig.parameters: call_kwargs["metadata"] = metadata
                    failures_ldf = rule_meta["func"](**call_kwargs)
                else:
                    failures_ldf = rule_meta["func"](ldf)
            elif registry_type == "lake":
                failures_ldf = rule_meta["func"](ldf, previous_ldf)
            elif registry_type == "registry":
                failures_ldf = rule_meta["func"](ldf, registry_ldf, metadata)
            else:
                return {"error": "Unknown registry type"}
        except Exception as e:
            return {"error": f"Logic failure during AI sample collection: {e}"}
        
        # 3. Cluster Sampling logic
        # We group by these core dimensions to find unique types of failures
        # Note: We use unique() on the collected samples to keep it fast
        sample_df = failures_ldf.unique(subset=["product_name", "customer_company_name", "rate_units"]).head(20).collect()
        
        if sample_df.height == 0:
            return {"error": f"No failures found for rule {rule_id} to analyze."}

        # 4. Dispatch to Audit Agent
        agent = RegulatoryAuditorAgent()
        analysis = agent.analyze_failure_pattern(
            rule_id=rule_id,
            rule_desc=rule_meta.get("description", "No description"),
            samples=sample_df
        )
        
        return analysis
