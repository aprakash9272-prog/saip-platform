from typing import List

from fastapi import APIRouter, Query, Response

from app.api.deps import SessionDep
from app.engine.coverage_engine import CoverageEngine
from app.engine.coverage_export import (
    export_coverage_excel,
    export_coverage_json,
    export_coverage_pdf,
)
from app.schemas.coverage import (
    CapabilityMatrix,
    CoverageReport,
    CoverageRequest,
    DomainCoverage,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])

_EXPORT_MEDIA_TYPES = {
    "json": "application/json",
    "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}
_EXPORT_EXTENSIONS = {"json": "json", "excel": "xlsx", "pdf": "pdf"}


@router.post(
    "/coverage",
    response_model=CoverageReport,
    summary="Calculate the coverage report for an assessment project",
)
def calculate_coverage(payload: CoverageRequest, session: SessionDep):
    return CoverageEngine(session).calculate(payload.assessment_project_id)


@router.get(
    "/coverage/{assessment_id}",
    response_model=CoverageReport,
    summary="Get the coverage report for an assessment project",
)
def get_coverage(assessment_id: int, session: SessionDep):
    return CoverageEngine(session).calculate(assessment_id)


@router.get(
    "/coverage/{assessment_id}/export",
    summary="Export the coverage report as JSON, Excel, or PDF",
)
def export_coverage(
    assessment_id: int,
    session: SessionDep,
    format: str = Query("json", pattern="^(json|excel|pdf)$"),
):
    report = CoverageEngine(session).calculate(assessment_id)
    if format == "excel":
        content = export_coverage_excel(report)
    elif format == "pdf":
        content = export_coverage_pdf(report)
    else:
        content = export_coverage_json(report)

    filename = f"coverage-{assessment_id}.{_EXPORT_EXTENSIONS[format]}"
    return Response(
        content=content,
        media_type=_EXPORT_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/domain-summary",
    response_model=List[DomainCoverage],
    summary="Domain-level coverage breakdown for an assessment project",
)
def domain_summary(assessment_id: int, session: SessionDep):
    report = CoverageEngine(session).calculate(assessment_id)
    return report.domain_coverage


@router.get(
    "/capabilities",
    response_model=CapabilityMatrix,
    summary="Capability coverage matrix (covered / missing / duplicate) for an assessment project",
)
def capability_matrix(assessment_id: int, session: SessionDep):
    report = CoverageEngine(session).calculate(assessment_id)
    return CapabilityMatrix(
        covered=report.covered_capabilities,
        missing=report.missing_capabilities,
        duplicate=report.duplicate_capabilities,
    )
