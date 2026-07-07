# Project Blueprint

## 1. Executive Summary

This document serves as the foundational blueprint for the Security Architecture Intelligence Platform (SAIP). It defines the product vision, architecture, requirements, engineering standards, and roadmap needed to guide implementation and long-term evolution.

## 2. Vision

SAIP aims to become the definitive open-source platform for understanding, analyzing, and optimizing enterprise security architecture across products, capabilities, controls, frameworks, and maturity.

## 3. Problem Statement

Security teams often struggle to answer critical questions about their architecture:

- What security capabilities do we currently have?
- Where are the gaps?
- Which tools overlap or are redundant?
- Which licenses are underutilized?
- Which capabilities were purchased but never enabled?
- Where can cost be reduced without increasing risk?

Existing tools typically focus on alerts, telemetry, or point solutions rather than providing a holistic architectural view.

## 4. Why Existing Tools Fail

Current security tooling often suffers from one or more of the following limitations:

- Reactive rather than strategic
- Fragmented data across vendors
- Poor cross-tool correlation
- Limited support for architectural reasoning
- Lack of explainability and traceability
- High cost and vendor lock-in

## 5. Product Goals

The platform should:

- Provide a unified view of the security ecosystem
- Identify capability gaps and overlaps
- Support evidence-based recommendations
- Improve maturity and governance outcomes
- Enable procurement and cost optimization decisions
- Support architecture simulation before implementation

## 6. User Personas

- Chief Information Security Officers (CISOs)
- Security Architects
- Security Engineers
- Security Operations Teams
- Risk and Compliance Teams
- IT Leadership
- Platform Administrators

## 7. Functional Requirements

The system should support:

- Ingestion of security product and capability data
- Mapping of products to frameworks and controls
- Detection of overlaps and duplicates
- Gap analysis across capability domains
- Maturity and coverage assessment
- Recommendation generation
- Scenario modeling and architecture simulations
- Search and exploration of knowledge base content
- Administrative configuration and user management

## 8. Non-Functional Requirements

- Offline-first capability where possible
- Open-source and extensible design
- Deterministic and explainable reasoning
- Privacy-preserving data handling
- High reliability and auditability
- Scalable architecture for enterprise data volumes
- Clear documentation and maintainability

## 9. Complete System Architecture

The platform will be composed of:

- A frontend experience for exploration and reporting
- A backend service layer for orchestration and business logic
- A knowledge base for structured and unstructured security domain knowledge
- An AI layer for recommendation and reasoning support
- A scoring and evaluation engine for maturity and overlap analysis
- A database layer for storing structured entities and relationships
- Integration layers for connectors and plugins

## 10. Frontend Architecture

The frontend should provide:

- Interactive dashboards
- Architecture visualization
- Search and filtering interfaces
- Recommendation views
- Admin and configuration panels
- Responsive and accessible UI components

## 11. Backend Architecture

The backend should provide:

- API services for data access and business operations
- Workflow orchestration
- Data validation and transformation pipelines
- Integration with connectors and plugins
- Audit logging and operational monitoring

## 12. AI Architecture

The AI architecture should support:

- Semantic understanding of security concepts
- Evidence-based reasoning and recommendation generation
- Explainable outputs with traceability to source data
- Optional offline or local inference where required
- Human-in-the-loop review of generated recommendations

## 13. Knowledge Base Design

The knowledge base will contain:

- Security product catalogs
- Capability definitions
- Framework mappings
- Control and maturity data
- Domain heuristics and rules
- Reference documentation and examples

## 14. Database Design

The database should store:

- Products and vendors
- Capabilities and relationships
- Frameworks and mappings
- Assessment records
- Recommendations and simulations
- User and admin metadata

## 15. API Design

The API should support:

- CRUD operations for core entities
- Search and filtering endpoints
- Analysis and recommendation endpoints
- Simulation and scenario execution endpoints
- Authentication and authorization services

## 16. Plugin Framework

The plugin framework should allow:

- Extensible ingestion of external data sources
- Custom analysis modules
- Optional integrations for specialized vendors or formats
- Safe, versioned plugin execution

## 17. Connector Framework

The connector framework should support:

- Integration with enterprise systems and repositories
- Structured data import and normalization
- Scheduled or event-driven synchronization
- Standardized logging and error handling

## 18. Security Principles

The platform must be built with:

- Secure authentication and authorization
- Least-privilege access
- Data minimization and privacy by design
- Encryption of sensitive data
- Audit trails for changes and operations
- Secure-by-default configuration

## 19. Deployment Architecture

Deployment should support:

- Containerized services
- Local or self-hosted installations
- Cloud deployment options where appropriate
- Scalable and observable infrastructure
- Clear backup and recovery procedures

## 20. Coding Standards

The codebase should follow:

- Consistent formatting and linting standards
- Clear modular architecture
- Comprehensive documentation
- Automated testing practices
- Version control discipline
- Review-based contributions

## 21. Git Strategy

The project should use:

- Mainline development with feature branches
- Small, reviewable pull requests
- Clear commit messaging
- Semantic versioning for releases

## 22. CI/CD

Continuous integration and delivery should include:

- Automated test execution
- Linting and static checks
- Build validation
- Release automation where applicable
- Environment-based deployment workflows

## 23. Roadmap

Planned phases include:

- Foundation and documentation
- Core data model and knowledge base
- Initial analysis and scoring engine
- UI and reporting experience
- Connector and plugin framework
- Advanced AI-assisted reasoning

## 24. Future Features

Potential future capabilities include:

- Deeper scenario simulation
- Formal control mapping and compliance workflows
- Multi-tenant enterprise support
- Advanced graph analytics
- Autonomous remediation recommendations
- Integration with broader security operations ecosystems

## 25. Implementation Status

Sprint-by-sprint delivery against this blueprint:

- **Sprint 2 — Project Foundation.** Docker Compose stack (FastAPI/SQLModel/Alembic + PostgreSQL, Next.js frontend), clean architecture layering, CI scaffolding.
- **Sprint 3 — Security Knowledge Base.** Vendor, Product, Edition, Module, Framework, FrameworkMapping entities; YAML knowledge base + idempotent importer/exporter.
- **Sprint 4 — Security Capability Catalog.** Domain taxonomy (18 domains) and vendor-neutral Capability catalog (324 capabilities), with YAML import/export and filter/facet APIs.
- **Sprint 5 — Product Capability Mapping.** `ProductCapabilityMapping` fact table linking vendor → product → edition → module → capability (licensing tier, supported platforms, deployment model, availability status), populated for 7 named vendors, with bulk-edit UI.
- **Sprint 6 — Customer Assessment Workspace.** Customer → Business Unit / Environment / Assessment Project → Product Assignment data model, referencing (never duplicating) the Sprint 5 knowledge base; an informational assessment dashboard; JSON export/import of assessments.
- **Sprint 7 — Coverage Analysis Engine.** The first real analysis engine: `CoverageEngine` calculates covered/missing/duplicate capabilities and per-domain/overall coverage percentages for an assessment project, counting only `Deployed` product assignments. Exposed via `/analysis/*` APIs with JSON/Excel/PDF export, and a Coverage Analysis dashboard (score, charts, heatmap, capability matrix) on the Assessment Project page. Pure calculation only — no gap remediation, overlap scoring, or recommendations.
- **Sprint 8 — Gap Analysis Engine.** Built directly on the Coverage Engine: `GapEngine` takes the missing-capability list and classifies each gap by severity (Critical/High/Medium/Low/Informational, from risk category + framework mapping count + a new `is_business_critical` capability flag), business impact, affected framework controls, and candidate catalog products. Per-domain and overall risk scores round out the report. Exposed via `/analysis/gaps*` APIs with JSON/Excel/PDF export, and a dedicated Gap Analysis page (executive summary, critical gap cards, domain risk heatmap, severity × business-impact risk matrix, filterable/sortable/searchable gap table, charts). Identification and classification only — no remediation recommendations.
- **Sprint 9 — Security Recommendation Engine.** Built directly on the Gap Engine: `RecommendationEngine` looks up every `ProductCapabilityMapping` catalog candidate for each gap and computes, deterministically (no AI/LLM), a confidence score, implementation complexity, estimated effort, and a 4-tier priority (Critical/High/Medium/Low, from severity + business criticality + framework impact + implementation effort). Also produces a coverage improvement forecast, a priority matrix, a cross-gap product comparison, and per-gap/overall estimated risk reduction. Exposed via `/analysis/recommendations*` APIs with JSON/Excel/PDF export, and a dedicated Recommendations page (executive summary, top recommendations, coverage forecast, priority matrix, product comparison, filterable/sortable/searchable recommendation table).

Overlap, Simulation, and AI Assistant engines (Sections 9–13) are intentionally not yet implemented — Sprints 3–9 exist to build the knowledge base, customer workspace, and coverage/gap/recommendation calculation those engines will consume or complement.
