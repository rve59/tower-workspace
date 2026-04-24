# TOWER SDLC Policy Master

This document defines the strict, isolated SDLC standards and workflow model for the **TOWER Ecosystem** (`TOWER_WORKSPACE`). It governs the development of the core application (`tower.core`) and all dedicated sub-libraries (`ferc.libs`, `xbrl.libs`, `agent.libs`).

- **Current Policy Version:** v1.0.0 (Isolated)
- **Scope:** TOWER Project Exclusively
- **Last Updated:** 2026-04-14

## The "Lean & Agentic" Workflow Model
TOWER operates under a strict, headcount-minimized engineering philosophy requiring human authorization at key validation gates while delegating testing and initial QA to agentic pipelines.

`research -> checkout branch -> feature -> design -> agent-test -> [AUTHORIZATION GATE] -> implementation/test -> commit -> manual-auth -> merge -> push`

> [!IMPORTANT]
> **Mandatory Authorization Gat**e: The transition from the "Design" phase to the "Implementation/Execution" phase requires **explicit human authorization**. The completion of research, feature definitions, or technical designs does NOT grant automatic permission to proceed with code implementation.

## Documentation Standards

### 1. Naming Convention
All documentation and artifacts must follow the `type_name_compositeID` format using 2-digit indexing concatenated on a base 6-digit root.
- **Research**: `research_<name>_<root_num>` (e.g., `research_architecture_000116`)
- **Feature**: `feature_<name>_<root_num><feature_num>`
- **Functional Design**: `fdesign_<name>_<feature_num><fdesign_num>`
- **Technical Design**: `tdesign_<name>_<fdesign_num><tdesign_num>`
- **Test Suite**: `test_suite_<name>_<tdesign_num><test_suite_num>`

### 2. Directory Structure (projmgt/)
Every library or core component within `TOWER_WORKSPACE` must maintain the following alignment in its `asdlc/` directory:
- `architecture/`
- `business/`
- `marketing/`
- `product/`
- `projmgt/01_research/`
- `projmgt/02_features/`
- `projmgt/03_fdesign/`
- `projmgt/04_tdesign/`
- `projmgt/05_test_suites/`

### 3. Safety & Math Formulation
To prevent parsing errors across the compliance stack:
- **Restriction**: LaTeX script (`$`, `$$`) and Unicode escape codes (e.g., `\u00A9`) are strictly PROHIBITED in the main body of a markdown file.
- **Requirement**: Use direct **Unicode symbols** for all mathematical and logical expressions (e.g., `∑`, `→`, `β`).
- **Exception**: LaTeX script and Unicode escapes are allowed ONLY within triple-backtick (```) code blocks.
