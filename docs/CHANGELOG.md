# Changelog

All notable changes to this project are documented in this file.

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
