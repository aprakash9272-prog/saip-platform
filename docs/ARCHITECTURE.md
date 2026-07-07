# Architecture

This document describes how SAIP is actually built today. For product vision and long-term scope, see [PROJECT_BLUEPRINT.md](PROJECT_BLUEPRINT.md).

## System Overview

```
┌─────────────┐      HTTP/JSON      ┌──────────────┐      SQL      ┌────────────┐
│  Next.js 15  │ ------------------> │   FastAPI     │ ------------> │ PostgreSQL │
│  frontend    │ <------------------ │   backend     │ <------------ │            │
└─────────────┘                     └──────────────┘               └────────────┘
```

Three Docker Compose services: `frontend` (Next.js standalone server), `backend` (FastAPI/uvicorn, auto-migrates via `alembic upgrade head` on startup), `db` (PostgreSQL 16).

## Backend: Layered / Clean Architecture

Every entity flows through the same five layers, in `backend/app/`:

```
models/       SQLModel table definitions (the persistence model)
schemas/      Pydantic Create / Update / Read schemas (the API contract)
repositories/ Data access — a generic BaseRepository[T] (pagination, search,
              filtering, sorting) plus per-entity natural-key lookups
services/     Business rules — a generic BaseService[T] (delegates to the
              repository) plus per-entity validate_references /
              validate_duplicate hooks and any bespoke operations
              (e.g. dashboard aggregation, JSON export/import)
api/routes/   FastAPI routers — thin controllers with no business logic
```

Two router patterns coexist:
- **Generic factory** (`api/routes/factory.py` → `build_crud_router`) for entities with no extra filters or sub-routes (e.g. products, editions).
- **Bespoke routers** for entities needing custom filters, sub-routes, or read-shape projection (e.g. modules, product mappings, every Sprint 6 entity, and the Sprint 7-8 `/analysis` routes).

Route registration order matters where static and dynamic paths share a prefix: `/analysis/gaps/export`, `/analysis/gaps/summary`, and `/analysis/gaps/domains` are all registered *before* `/analysis/gaps/{assessment_id}` in `api/routes/analysis.py`, since FastAPI matches path operations in registration order and a dynamic segment would otherwise swallow the static ones.

Cross-cutting infrastructure shared by all entities:
- `PaginationParams` (`api/deps.py`): `skip`, `limit`, `search`, `sort_by`, `sort_desc` — applied uniformly by `BaseRepository.list()`.
- Custom exception hierarchy (`core/exceptions.py`): `EntityNotFoundError` → 404, `DuplicateEntityError` → 409, `InvalidReferenceError` → 422, registered as global FastAPI exception handlers.
- Enums (deployment model, deployment status, environment type, assessment status, etc.) are validated in the Pydantic layer via `field_validator`, not native DB enum types — stored as plain `VARCHAR` for easy evolution.

## Database Schema

```
Vendor ──< Product ──< Edition ──< Module >──< Capability >── Domain
                                       │              │
                                       │              └──< FrameworkMapping >── Framework
                                       │
Customer ──< BusinessUnit             │
    │                                 │
    ├──< Environment                 │
    │                                 │
    └──< AssessmentProject ──< ProductAssignment >── Module (M2M)
                                       │
                          references Vendor/Product/Edition/Environment
                          (never duplicates catalog data)
```

- `ProductCapabilityMapping` (Sprint 5) is the fact table joining the catalog hierarchy to capabilities, with licensing tier, supported platforms, deployment model, and availability status.
- `ProductAssignment` (Sprint 6) is the fact table joining an `AssessmentProject` to the catalog hierarchy, with a many-to-many `modules` relationship (via `ProductAssignmentModuleLink`), license quantity, deployment model, deployment status, and notes.
- `Capability.is_business_critical` (Sprint 8) is a boolean, defaulting to `false`, added specifically as a severity-classification input for the Gap Engine (see below) — set via the Capabilities API/UI or YAML import, alongside the pre-existing `risk_category`.
- Referential integrity is enforced at both the database level (foreign keys, unique constraints) and the service layer (`validate_references` cross-checks the hierarchy is internally consistent — e.g. a `ProductAssignment`'s product must belong to its vendor, and its environment must belong to the same customer as its assessment project).
- Migrations are managed with Alembic (`backend/alembic/versions/`); one revision per sprint's schema changes, applied automatically on container startup.

## Analysis Engines

`backend/app/engine/` holds the analysis layer described in Section 9 of the Project Blueprint — one module per engine, called from bespoke routes rather than the generic CRUD stack since engines compute derived reports, not persisted rows.

- `coverage_engine.py` (Sprint 7, implemented): `CoverageEngine.calculate(assessment_project_id)` reads the assessment project's `Deployed` product assignments, walks each assignment's modules → capabilities, and cross-references every `Capability` and `Domain` row in the catalog to produce a `CoverageReport` (covered/missing/duplicate capabilities, per-domain and overall coverage percentages). It is a read-only computation — nothing is written to the database, and repeated calls are idempotent and side-effect-free. `engine/coverage_export.py` renders that report as JSON, an `openpyxl` workbook, or a `reportlab` PDF.
- `gap_engine.py` (Sprint 8, implemented): `GapEngine.calculate(assessment_project_id)` calls `CoverageEngine` internally and takes its `missing_capabilities` list as the sole input — it does not recompute coverage. For each missing capability it looks up the `Capability` row (risk category, `is_business_critical`), its `framework_mappings` (for both a count used in severity scoring and the full control list surfaced on the gap), and scans `ProductCapabilityMapping` for candidate catalog products. Severity and business impact are computed by small pure functions (`_classify_severity`, `_classify_business_impact`) so the scoring logic is unit-testable in isolation from the ORM. Domain and overall risk scores are a deterministic blend (`(gap_percentage + average_severity_weight) / 2`) — see the module docstring for the exact weights. `engine/gap_export.py` mirrors `coverage_export.py`'s JSON/Excel/PDF pattern.
- `overlap_engine.py`, `recommendation_engine.py`, `simulation_engine.py`, `cost_engine.py` — placeholders (`raise NotImplementedError`) for future sprints.

## Frontend: Next.js App Router

```
src/app/(dashboard)/           route segments (App Router, one folder per page)
src/components/knowledge-base/ config-driven CRUD system shared by all catalog entities:
                                  resource-configs.ts  per-entity zod schema + column/field config
                                  resource-page.tsx     generic list/create/edit/delete page
                                  data-table.tsx, entity-form-dialog.tsx, entity-detail-sheet.tsx
src/components/customers/      Customer detail page + Business Unit/Environment/Assessment dialogs
src/components/assessments/    Assessment project page, Product Assignment wizard, the Coverage
                                Analysis section, and the dedicated Gap Analysis page (executive
                                summary, critical gap cards, risk heatmap, risk matrix, filterable/
                                sortable gap table, charts)
src/lib/api/                   typed fetch client, per-entity resource functions, shared TS types
src/hooks/                     useResourceQueries (list/create/update/delete via TanStack Query),
                                useResourceOptions (reference dropdowns), useReferenceMaps (id -> label)
```

Flat catalog entities (vendors, products, customers, ...) go through the generic config-driven `ResourcePage`. Entities with nested detail views, cross-entity dashboards, cascading selection (vendor → product → edition → module), file import/export, or computed reports (Customer, Assessment Project, Product Assignment, Capabilities, Product Mappings, Coverage Analysis, Gap Analysis) use bespoke page components that compose the same shared UI primitives (`Dialog`, `Table`, `Card`, shadcn/ui) directly, plus `recharts` for charts. The Gap Analysis page (`/assessments/{id}/gaps`) is a standalone route rather than an embedded section — search/filter/sort state for a full gap table warranted its own page instead of crowding the Assessment Project page further.

The `FieldConfig` type in the generic config-driven CRUD system gained a `"boolean"` field type in Sprint 8 (rendered as a checkbox in `entity-form-dialog.tsx`), used by the Capabilities form for `is_business_critical` — the first boolean field in that system.

## What's Deliberately Not Built Yet

Sections 9–13 of the [Project Blueprint](PROJECT_BLUEPRINT.md) describe a Coverage Engine, Gap Engine, Overlap Engine, Recommendation Engine, Simulation Engine, and AI Assistant. The Coverage and Gap Engines are implemented as of Sprints 7-8 (see above) — the other four are still `NotImplementedError` placeholders in `app/engine/`. Sprints 3–8 exist to build the knowledge base, the customer assessment workspace, and now coverage/gap calculation; overlap/redundancy scoring, remediation recommendations, simulation, and AI reasoning are future sprints.
