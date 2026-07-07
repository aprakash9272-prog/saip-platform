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
- **Bespoke routers** for entities needing custom filters, sub-routes, or read-shape projection (e.g. modules, product mappings, every Sprint 6 entity, and the Sprint 7-10 `/analysis` routes).

Route registration order matters where static and dynamic paths share a prefix: within `api/routes/analysis.py`, each analysis resource's `export`/`summary` (and, for gaps, `domains`) sub-routes are registered *before* its dynamic `/{assessment_id}` (or, for simulation, `/{simulation_id}`) route — `/analysis/gaps/*`, `/analysis/recommendations/*`, `/analysis/overlap/*`, and `/analysis/simulation/*` all follow this pattern, since FastAPI matches path operations in registration order and a dynamic segment would otherwise swallow the static ones.

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
- `recommendation_engine.py` (Sprint 9, implemented): `RecommendationEngine.calculate(assessment_project_id)` calls `GapEngine` internally and treats its `gaps` list as the sole source of truth — it never recomputes coverage or gaps itself. For each gap it scans every `ProductCapabilityMapping` row matching that capability_id (regardless of whether that vendor is deployed in this assessment) and turns each into a `ProductCandidate`, computed by pure functions (`_confidence_score`, `_implementation_complexity`, `_classify_priority`) that take only primitive inputs — no AI/LLM calls, no ORM access — so the scoring logic is unit-testable in isolation. A gap's "already deployed vendor" signal comes from cross-referencing the assessment's `Deployed` `ProductAssignment` rows' `vendor_id` against each candidate's vendor. Per-gap `estimated_risk_reduction` is computed by re-running the same aggregate risk-score formula `GapEngine` uses, once with that gap removed from the totals — a real marginal-impact calculation, not a heuristic label. `engine/recommendation_export.py` mirrors the JSON/Excel/PDF pattern of the other two engines.
- `overlap_engine.py` (Sprint 10, implemented): `OverlapEngine.calculate(assessment_project_id)` instantiates `CoverageEngine`, `GapEngine`, and `RecommendationEngine` directly (each still recomputes independently — there's no shared-report-passing between engines yet, an accepted redundancy given each `.calculate()` call is cheap) and combines them: coverage's covered-capability set for the duplicate-detection baseline, the gap report's `overall_gap_percentage` as one input to the optimization score, and the recommendation report's `product_comparison` to flag which overlapping vendors also address open gaps. Duplicate/product/module overlap detection walks each deployed assignment's *enabled* modules only (not the full edition), so "unused capabilities" — modules that come with the license but were never turned on — falls out naturally by diffing enabled vs. all-modules-under-the-edition. All pairwise comparisons (product overlap, module overlap) use `itertools.combinations` over the deployed set, bounded by assessment size in practice. `engine/overlap_export.py` mirrors the JSON/Excel/PDF pattern of the other engines.
- `simulation_engine.py` (Sprint 11, implemented): `SimulationEngine.simulate(request)` runs `CoverageEngine`, `GapEngine`, `RecommendationEngine`, and `OverlapEngine` unmodified twice — once against the assessment's real current state, once again after applying one hypothetical `SimulationRequest` mutation — and diffs the two sets of reports into ten `MetricComparison` deltas plus capability/vendor/framework comparison tables. The mutation itself is applied to plain ORM objects via `session.add()` / `session.delete()` / `session.flush()` — **never `session.commit()`** — and a `finally` block unconditionally calls `session.rollback()` before returning, so the real assessment is never modified regardless of whether the scenario application succeeds. This was verified empirically against both SQLite and PostgreSQL: `session.commit()` (what `BaseRepository.create/update/delete` call internally) persists durably even inside a SAVEPOINT, while `flush()` + `rollback()` never does — which is why the engine reuses only `ProductAssignmentService`'s non-committing validation helpers (`validate_references`, `validate_duplicate`, `_resolve_modules`) rather than its committing CRUD methods. All 12 scenario types reduce to a handful of primitive mutations (add/remove/swap-edition/toggle-module/change-field/bulk-remove) on `ProductAssignment`. Only the final computed `SimulationReport` is durably persisted, as a `SimulationRun` row (`app/models/simulation_run.py`) — purely so `GET /analysis/simulation/{id}` can retrieve a past run later; the row stores no assessment mutation, only the read-only report JSON. `engine/simulation_export.py` mirrors the JSON/Excel/PDF pattern of the other engines.
- `cost_engine.py` — placeholder (`raise NotImplementedError`) for a future sprint.

## Frontend: Next.js App Router

```
src/app/(dashboard)/           route segments (App Router, one folder per page)
src/components/knowledge-base/ config-driven CRUD system shared by all catalog entities:
                                  resource-configs.ts  per-entity zod schema + column/field config
                                  resource-page.tsx     generic list/create/edit/delete page
                                  data-table.tsx, entity-form-dialog.tsx, entity-detail-sheet.tsx
src/components/customers/      Customer detail page + Business Unit/Environment/Assessment dialogs
src/components/assessments/    Assessment project page, Product Assignment wizard, the Coverage
                                Analysis section, the Gap Analysis page, the Recommendations page,
                                the Overlap page (vendor comparison, overlap matrix, capability
                                heatmap, duplicate products, optimization opportunities), and the
                                Simulation page (scenario builder, current-vs-proposed metrics,
                                before/after charts, comparison tables)
src/lib/api/                   typed fetch client, per-entity resource functions, shared TS types
src/hooks/                     useResourceQueries (list/create/update/delete via TanStack Query),
                                useResourceOptions (reference dropdowns), useReferenceMaps (id -> label)
```

Flat catalog entities (vendors, products, customers, ...) go through the generic config-driven `ResourcePage`. Entities with nested detail views, cross-entity dashboards, cascading selection (vendor → product → edition → module), file import/export, or computed reports (Customer, Assessment Project, Product Assignment, Capabilities, Product Mappings, Coverage Analysis, Gap Analysis, Recommendations, Overlap, Simulation) use bespoke page components that compose the same shared UI primitives (`Dialog`, `Table`, `Card`, shadcn/ui) directly, plus `recharts` for charts. The Gap Analysis, Recommendations, Overlap, and Simulation pages (`/assessments/{id}/gaps`, `/recommendations`, `/overlap`, `/simulation`) are standalone routes rather than embedded sections — search/filter/sort state for a full table (or, for Simulation, a multi-field scenario builder plus a full set of comparison views) warranted its own page instead of crowding the Assessment Project page further.

The `FieldConfig` type in the generic config-driven CRUD system gained a `"boolean"` field type in Sprint 8 (rendered as a checkbox in `entity-form-dialog.tsx`), used by the Capabilities form for `is_business_critical` — the first boolean field in that system.

## What's Deliberately Not Built Yet

Sections 9–13 of the [Project Blueprint](PROJECT_BLUEPRINT.md) describe a Coverage Engine, Gap Engine, Overlap Engine, Recommendation Engine, Simulation Engine, and AI Assistant. The Coverage, Gap, Recommendation, Overlap, and Simulation Engines are implemented as of Sprints 7-11 (see above) — only the AI Assistant remains a future concern (there is no `NotImplementedError` placeholder for it yet in `app/engine/`, since nothing AI-related has been scaffolded). Sprints 3–11 exist to build the knowledge base, the customer assessment workspace, and coverage/gap/recommendation/overlap/simulation calculation, all of it deterministic and rule-based; AI-assisted reasoning is a future sprint.
