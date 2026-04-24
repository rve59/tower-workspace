---

kanban-plugin: board

---

## Unplanned

- [ ] Multi-Output Bridge research for Gen 2 #unplanned
- [ ] Advanced Semantic Reconciliation modules #unplanned


## Plan Stage 4: High-Performance MVP (Weeks 7-8)

- [ ] Implement Virtual-scrolling Data Grid in React #stage/4
- [ ] Stream Polars/Parquet data to Frontend via WebSockets/REST #stage/4
- [ ] Finalize "Mechanical Proof" export (XBRL-CSV) #stage/4
- [ ] End-to-end integration testing (`tests/integration`) #stage/4
- [ ] Performance optimization for massive trade log rendering #stage/4


## Plan Stage 3: Validation & UI (Weeks 5-6)

- [ ] Implement `lib_tower_telemetry` for Gen 3 training data #backlog
- [ ] Develop `xbrl.libs/lib_xbrl_ladybug_bridge` #stage/3
- [ ] Integrate Ladybug engine with mapped FERC data #stage/3
- [ ] Build Q&A dynamic interface for schema mapping #stage/3
- [ ] Implement real-time "Pre-Audit Shield" scorecard #stage/3
- [ ] Map "Young Filer" inputs to XBRL schema nodes #stage/3


## Plan Stage 2: Logic & Integration (Weeks 3-4)

- [ ] Build React "Young Filer" Onboarding Wizard #stage/2
- [ ] Implement `ferc.libs/lib_ferc_rules` (Form 1/714 Intersections) #stage/2
- [ ] Connect FastAPI endpoints to `lib_tower_k_ingest` #stage/2
- [ ] Create drag-and-drop file upload UI component #stage/2
- [ ] Implement user session/workspace isolation in API #stage/2


## Plan MVP: Arelle Adapter & Log Capture

- [ ] Register `CntlrCmdLine.Options` hook for `--tower-enhanced` flag #mvp/arelle #stage/mvp
- [ ] Register `Validate.Validate` hook to intercept FERC validation #mvp/arelle #stage/mvp
- [ ] Implement `TowerLogHandler` — Arelle log format parity #mvp/arelle #stage/mvp
- [ ] Implement enhanced diagnostics overlay for `--tower-enhanced` mode #mvp/arelle #stage/mvp
- [ ] Log parity integration test (diff TOWER vs native Arelle output) #mvp/arelle #stage/mvp


## Plan MVP: FastAPI Ingestion Service

- [ ] Implement workspace/session isolation (UUID scoping) #mvp/api #stage/mvp
- [ ] Implement `TelemetryRecord` Pydantic model #mvp/api #stage/mvp
- [ ] Register ingestion start time (Req 4.3.02) #mvp/api #stage/mvp
- [ ] Record payload metadata: user, timestamp, source size (Req 4.3.01) #mvp/api #stage/mvp


## Plan MVP: Polars / Parquet Pipeline

- [ ] Implement Parquet serialization from raw source data #stage/1
- [ ] Initialize `ingest.libs/lib_tower_k_ingest` with Polars #stage/1
- [ ] Implement Polars CSV → Parquet conversion worker (Req 4.4.02) #mvp/parquet #stage/mvp
- [ ] Implement Polars Excel → Parquet conversion worker (Req 4.4.03) #mvp/parquet #stage/mvp
- [ ] Register parquet conversion start/end times (Req 4.4.01 / 4.4.06) #mvp/parquet #stage/mvp
- [ ] Implement schema-enforced data type validation + error list (Req 4.4.05) #mvp/parquet #stage/mvp
- [ ] Convert Polars DataFrame → TOWER-K edge/graph format (Req 4.5.02) #mvp/parquet #stage/mvp
- [ ] Register TOWER-K ingestion start/end times (Req 4.5.01 / 4.5.04) #mvp/parquet #stage/mvp
- [ ] Structural validation of TOWER-K model vs. ERQ schema (Req 4.5.03) #mvp/parquet #stage/mvp


## Plan MVP: XULE / X2C Transpiler

- [ ] Define ERQ XULE rule subset for MVP transpilation (Req 3) #mvp/xule #stage/mvp
- [ ] Implement XULE grammar parser (assert, rule-name, fact-value patterns) #mvp/xule #stage/mvp
- [ ] Transpile XULE rules → Polars filter expressions (X2C) (Req 4.6.02) #mvp/xule #stage/mvp
- [ ] Execute transpiled rules against TOWER-K model (Req 4.6.04) #mvp/xule #stage/mvp
- [ ] Map XULE errors → Arelle log format (EFM.x.xx.xx style) (Req 4.6.05) #mvp/xule #stage/mvp
- [ ] Register XULE validation start/end times (Req 4.6.01 / 4.6.06) #mvp/xule #stage/mvp


## FERC CSV Historical

- [ ] Implement Historical Ingestion: FERC Form 1 #historical #ferc
- [ ] Implement Historical Ingestion: FERC Form 2 #historical #ferc
- [ ] Implement Historical Ingestion: FERC Form 6 #historical #ferc
- [ ] Implement Historical Ingestion: FERC Form 60 #historical #ferc
- [ ] Implement Historical Ingestion: FERC Form 714 #historical #ferc
- [x] Implement Historical Ingestion: FERC EQR (Pre-XBRL) #historical #eqr


## Backlog

- [ ] Audit Arelle CLI arg spec (--logFile, --validate, -f) #mvp/arelle #stage/mvp
- [ ] Implement `tower_plugin.py` Arelle plugin entry point #mvp/arelle #stage/mvp


## Design Features

- [ ] Scaffold FastAPI server in `apps/api` #stage/1
- [ ] Install and Setup Ladybug system #stage/mvp
- [ ] Implement `POST /v1/ingest/upload` multipart file endpoint #mvp/api #stage/mvp


## FDesign

- [ ] Scaffold FastAPI app in `tower.core/apps/api` (main.py, routers, config) #mvp/api #stage/mvp


## Development



## Testing



## Done

- [ ] Create `lib_ui_industrial` design tokens (Industrial-Clean) #stage/1
- [x] write a UI/UX specifiction language for the TOWER App #stage/1
- [x] Define TOWER System Architecture & Strategy #done
- [x] Establish Global SDLC Policy & 6-Digit Registry #done
- [x] Scaffold `tower.core` directory structure #done
- [x] Finalize Gen 1 Project Plan (000103) #done
- [x] MVP Ideation: WBS Work Breakdown (5d32b059) #done
- [ ] Design UI UX for ingestion and validation features #stage/1 @{2026-04-15} ^vhjdbh
- [ ] [[Initialize React SPA with Tailwind in `apps frontend` stage 1]]




%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[true,true,true,true,false,null,null,null,false,null,null,true,true,true],"move-tags":true,"show-checkboxes":false,"new-line-trigger":"enter"}
```
%%