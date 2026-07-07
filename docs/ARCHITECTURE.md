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
- **Bespoke routers** for entities needing custom filters, sub-routes, or read-shape projection (e.g. modules, product mappings, and every Sprint 6 entity).

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
- Referential integrity is enforced at both the database level (foreign keys, unique constraints) and the service layer (`validate_references` cross-checks the hierarchy is internally consistent — e.g. a `ProductAssignment`'s product must belong to its vendor, and its environment must belong to the same customer as its assessment project).
- Migrations are managed with Alembic (`backend/alembic/versions/`); one revision per sprint's schema changes, applied automatically on container startup.

## Frontend: Next.js App Router

```
src/app/(dashboard)/           route segments (App Router, one folder per page)
src/components/knowledge-base/ config-driven CRUD system shared by all catalog entities:
                                  resource-configs.ts  per-entity zod schema + column/field config
                                  resource-page.tsx     generic list/create/edit/delete page
                                  data-table.tsx, entity-form-dialog.tsx, entity-detail-sheet.tsx
src/components/customers/      Customer detail page + Business Unit/Environment/Assessment dialogs
src/components/assessments/    Assessment project page + Product Assignment wizard
src/lib/api/                   typed fetch client, per-entity resource functions, shared TS types
src/hooks/                     useResourceQueries (list/create/update/delete via TanStack Query),
                                useResourceOptions (reference dropdowns), useReferenceMaps (id -> label)
```

Flat catalog entities (vendors, products, customers, ...) go through the generic config-driven `ResourcePage`. Entities with nested detail views, cross-entity dashboards, cascading selection (vendor → product → edition → module), or file import/export (Customer, Assessment Project, Product Assignment, Capabilities, Product Mappings) use bespoke page components that compose the same shared UI primitives (`Dialog`, `Table`, `Card`, shadcn/ui) directly.

## What's Deliberately Not Built Yet

Sections 9–13 of the [Project Blueprint](PROJECT_BLUEPRINT.md) describe a Coverage Engine, Gap Engine, Overlap Engine, Recommendation Engine, Simulation Engine, and AI Assistant. None of these exist yet. Sprints 3–6 exist solely to build the knowledge base (vendors/products/capabilities/frameworks) and the customer assessment workspace (customers/environments/assessment projects/product assignments) that those engines will read from — the assessment dashboard is explicitly informational-only, with no scoring logic.
