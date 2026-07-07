# Changelog

All notable changes to this project are documented in this file.

## [v0.8.0-alpha] — 2026-07-07 — Security Recommendation Engine

### Added
- `RecommendationEngine` (`app/engine/recommendation_engine.py`), built directly on `GapEngine`: recommends the catalog products, modules, and configurations that would close every addressable gap. Fully deterministic and knowledge-base-driven — no AI/LLM reasoning, no generated text.
- For every gap, every matching `ProductCapabilityMapping` catalog row becomes a candidate recommendation with a confidence score (from availability status, +15 if the vendor is already deployed elsewhere in the assessment), implementation complexity (from deployment model, downgraded a tier for an already-deployed vendor), estimated effort, required license tier, deployment model, and platform support.
- Deterministic 4-tier priority ranking (Critical/High/Medium/Low) from gap severity, business impact, framework-control count, the best candidate's implementation complexity, and whether closing the gap meaningfully moves an unusually small domain's coverage.
- Per-gap `estimated_risk_reduction`: the precise marginal delta in the assessment's overall risk score if that one gap were closed, computed by re-running the Gap Engine's own risk-score formula with the gap removed — not a qualitative label.
- Report-level coverage improvement forecast (current vs. projected coverage % if every addressable gap were closed), a priority matrix, and a cross-gap product comparison (which catalog products address the most gaps).
- Gaps with zero catalog candidates are counted as unaddressable and produce no recommendation.
- `POST /analysis/recommendations`, `GET /analysis/recommendations/{assessment_id}`, `GET /analysis/recommendations/export` (JSON/Excel/PDF), `GET /analysis/recommendations/summary`, documented in Swagger.
- A dedicated Recommendations page (`/assessments/{id}/recommendations`, linked from the Assessment Project page): executive summary, coverage improvement forecast bar, Top Recommendations card grid, a priority-matrix bar chart, a product comparison table, and a recommendation table with search, priority/domain filters, and sortable columns.
- Unit tests for confidence/complexity/priority scoring and risk-reduction calculation, API integration tests for all four endpoints and every export format (plus a route-ordering regression guard), and a performance test reusing the Sprint 8 bulk-catalog fixture (171 backend tests total, all passing).

## [v0.7.0-alpha] — 2026-07-07 — Gap Analysis Engine

### Added
- `GapEngine` (`app/engine/gap_engine.py`), built directly on `CoverageEngine`: identifies and classifies every missing capability from an assessment's coverage report. Pure identification/classification — no remediation recommendations.
- Deterministic severity classification (Critical/High/Medium/Low/Informational) from a capability's risk category, its framework mapping count, and a new `is_business_critical` flag; a related but distinct business-impact classification (Severe/High/Moderate/Low).
- `Capability.is_business_critical` boolean field (default `false`), added as a Gap Engine severity input — settable via the Capabilities API/UI or YAML import/export, alongside the existing `risk_category`.
- Each gap includes the compliance framework controls mapped to it and candidate catalog products (from `ProductCapabilityMapping`) known to provide it, plus a fixed `"Open"` status.
- Per-domain gap scores (coverage %, gap %, missing count, critical gap count, a blended 0-100 domain risk score) across all 18 domains, plus an overall gap percentage and risk score for the assessment.
- `POST /analysis/gaps`, `GET /analysis/gaps/{assessment_id}`, `GET /analysis/gaps/export`, `GET /analysis/gaps/summary`, `GET /analysis/gaps/domains`, all documented in Swagger.
- Excel (`openpyxl`, Summary/Domain Gap Scores/Gaps sheets) and PDF (`reportlab`, paginated) export, alongside JSON.
- A dedicated Gap Analysis page (`/assessments/{id}/gaps`, linked from the Assessment Project page): executive summary, Critical Gap card grid, gaps-by-severity and gaps-by-domain bar charts, a domain risk heatmap, a severity × business-impact risk matrix, and a gap table with search, severity/domain filters, sortable columns, and JSON/Excel/PDF export.
- A `"boolean"` field type in the generic config-driven CRUD form system (`entity-form-dialog.tsx`), used by the Capabilities form for `is_business_critical`.
- Unit tests for severity/business-impact classification and domain/overall risk scoring, API integration tests for all five endpoints and all three export formats (plus a route-ordering regression guard for the static-vs-dynamic `/gaps/*` paths), and a performance test seeding a ~360-capability/60-assignment catalog with framework mappings and product mappings (152 backend tests total, all passing).

## [v0.6.0-alpha] — 2026-07-07 — Coverage Analysis Engine

### Added
- `CoverageEngine` (`app/engine/coverage_engine.py`): the first real analysis engine, calculating capability coverage for an assessment project from its `Deployed` product assignments. Not Started, In Progress, and Decommissioned assignments do not count — only what is actually deployed today contributes coverage.
- Coverage calculation determines, for every capability in the catalog: covered / missing / duplicate status and the deployed products providing it. Duplicates are counted per distinct deployed product, so multiple modules on the same product providing the same capability are not flagged as redundant.
- Domain-level coverage (covered/total/percentage) across all 18 security domains, plus an overall coverage percentage for the assessment.
- `GET /analysis/coverage/{assessment_id}`, `POST /analysis/coverage`, `GET /analysis/domain-summary`, `GET /analysis/capabilities`, and `GET /analysis/coverage/{assessment_id}/export?format=json|excel|pdf`.
- Excel (`openpyxl`) and PDF (`reportlab`) export of the coverage report, alongside JSON.
- Frontend Coverage Analysis section on the Assessment Project page: a coverage score card, covered/missing/duplicate summary cards, a covered-vs-missing pie chart, a per-domain coverage bar chart, a domain heatmap, a filterable capability matrix table, and JSON/Excel/PDF export buttons (using `recharts`).
- Unit tests for the engine's coverage/duplicate-detection logic, API integration tests for all five endpoints and all three export formats, and a performance test seeding a ~360-capability, 60-assignment catalog directly at the model layer.

## [v0.5.0-alpha] — 2026-07-07 — Customer Assessment Workspace

### Added
- `Customer`, `BusinessUnit`, `Environment` (Production/UAT/Development/DR/OT), and `AssessmentProject` models with full CRUD, referential integrity, and duplicate prevention.
- `ProductAssignment` model linking an Assessment Project to an existing Vendor/Product/Edition (+ Modules) from the Sprint 5 knowledge base, with license quantity, deployment model, deployment status, environment, and notes. Cross-hierarchy validation ensures the product belongs to the vendor, the edition to the product, each module to the edition, and the environment to the same customer as the assessment project. A unique constraint on `(assessment_project, edition, environment)` prevents duplicate assignments.
- Informational assessment dashboard (`GET /assessment-projects/{id}/dashboard`) summarizing total deployed products, vendors in use, modules enabled, capabilities available, security domains represented, and frameworks represented — no coverage/gap/overlap scoring.
- JSON export/import of an assessment project and its product assignments (`GET/POST /assessment-projects/{id}/export`, `POST /assessment-projects/import`), keyed by natural names and idempotent on re-import.
- REST APIs for Customers, Business Units, Environments, Assessment Projects, and Product Assignments — pagination, search, filtering, and sorting, documented in Swagger.
- Generic `sort_by`/`sort_desc` query parameters added to every list endpoint across the platform.
- Frontend: Customer list and detail pages (business units, environments, assessment projects), an Assessment Project page (dashboard, product assignments table, import/export), and a two-step Product Assignment wizard.
- Alembic migration for `customer`, `business_unit`, `environment`, `assessment_project`, `product_assignment`, and `product_assignment_module_link` tables.
- Backend unit and API test coverage for all new entities, the dashboard, and export/import round-trips.

## [v0.4.0-alpha] — 2026-07-07 — Product Capability Mapping

### Added
- `ProductCapabilityMapping` fact table linking vendor → product → edition → module → capability, with licensing tier, supported platforms, deployment model, and availability status.
- Populated with 16 mappings across 7 named vendors (CrowdStrike, Microsoft, SentinelOne, Trellix, Palo Alto Networks, Okta, Splunk).
- Facet, YAML export/import, and bulk update/delete endpoints for product mappings; bulk-edit UI on the frontend.

## [v0.3.0-alpha] — 2026-07-06 — Security Capability Catalog

### Added
- Security domain taxonomy (18 domains) and vendor-neutral Capability catalog (324 capabilities).
- YAML import/export for domains and capabilities, with domain/risk-category filtering and facets.

## [v0.2.0-alpha] — 2026-07-06 — Security Knowledge Base

### Added
- Vendor, Product, Edition, Module, Framework, and FrameworkMapping entities with full CRUD.
- YAML-based knowledge base with an idempotent importer/exporter (`import_all` / `export_all`).

## [v0.1.0-alpha] — 2026-07-06 — Project Foundation

### Added
- Docker Compose stack: FastAPI + SQLModel + Alembic backend, PostgreSQL, Next.js 15 + TypeScript + Tailwind + shadcn/ui frontend.
- Clean architecture layering (models → schemas → repositories → services → API routes).
