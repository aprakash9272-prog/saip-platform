from typing import List

from fastapi import APIRouter, Query, Response

from app.api.deps import SessionDep
from app.engine.coverage_engine import CoverageEngine
from app.engine.coverage_export import (
    export_coverage_excel,
    export_coverage_json,
    export_coverage_pdf,
)
from app.engine.gap_engine import GapEngine
from app.engine.gap_export import export_gap_excel, export_gap_json, export_gap_pdf
from app.engine.recommendation_engine import RecommendationEngine
from app.engine.recommendation_export import (
    export_recommendation_excel,
    export_recommendation_json,
    export_recommendation_pdf,
)
from app.schemas.coverage import (
    CapabilityMatrix,
    CoverageReport,
    CoverageRequest,
    DomainCoverage,
)
from app.schemas.gap import DomainGapScore, GapReport, GapRequest, GapSummary
from app.schemas.recommendation import (
    RecommendationReport,
    RecommendationRequest,
    RecommendationSummary,
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


# --------------------------------------------------------------- Gap Analysis --
# Static sibling paths (export/summary/domains) must be registered before the
# dynamic /gaps/{assessment_id} route below, or FastAPI would try to parse
# "export"/"summary"/"domains" as an assessment_id.


@router.post(
    "/gaps",
    response_model=GapReport,
    summary="Calculate the gap report for an assessment project",
)
def calculate_gaps(payload: GapRequest, session: SessionDep):
    return GapEngine(session).calculate(payload.assessment_project_id)


@router.get(
    "/gaps/export",
    summary="Export the gap report as JSON, Excel, or PDF",
)
def export_gaps(
    session: SessionDep,
    assessment_id: int,
    format: str = Query("json", pattern="^(json|excel|pdf)$"),
):
    report = GapEngine(session).calculate(assessment_id)
    if format == "excel":
        content = export_gap_excel(report)
    elif format == "pdf":
        content = export_gap_pdf(report)
    else:
        content = export_gap_json(report)

    filename = f"gaps-{assessment_id}.{_EXPORT_EXTENSIONS[format]}"
    return Response(
        content=content,
        media_type=_EXPORT_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/gaps/summary",
    response_model=GapSummary,
    summary="Executive summary of the gap report for an assessment project",
)
def gap_summary(assessment_id: int, session: SessionDep):
    report = GapEngine(session).calculate(assessment_id)
    return GapSummary(**report.model_dump(exclude={"domain_gap_scores", "gaps"}))


@router.get(
    "/gaps/domains",
    response_model=List[DomainGapScore],
    summary="Domain-level gap breakdown for an assessment project",
)
def gap_domain_summary(assessment_id: int, session: SessionDep):
    report = GapEngine(session).calculate(assessment_id)
    return report.domain_gap_scores


@router.get(
    "/gaps/{assessment_id}",
    response_model=GapReport,
    summary="Get the gap report for an assessment project",
)
def get_gaps(assessment_id: int, session: SessionDep):
    return GapEngine(session).calculate(assessment_id)


# ----------------------------------------------------------- Recommendations --
# Static sibling paths (export/summary) must be registered before the dynamic
# /recommendations/{assessment_id} route below, same reasoning as /gaps above.


@router.post(
    "/recommendations",
    response_model=RecommendationReport,
    summary="Calculate the recommendation report for an assessment project",
)
def calculate_recommendations(payload: RecommendationRequest, session: SessionDep):
    return RecommendationEngine(session).calculate(payload.assessment_project_id)


@router.get(
    "/recommendations/export",
    summary="Export the recommendation report as JSON, Excel, or PDF",
)
def export_recommendations(
    session: SessionDep,
    assessment_id: int,
    format: str = Query("json", pattern="^(json|excel|pdf)$"),
):
    report = RecommendationEngine(session).calculate(assessment_id)
    if format == "excel":
        content = export_recommendation_excel(report)
    elif format == "pdf":
        content = export_recommendation_pdf(report)
    else:
        content = export_recommendation_json(report)

    filename = f"recommendations-{assessment_id}.{_EXPORT_EXTENSIONS[format]}"
    return Response(
        content=content,
        media_type=_EXPORT_MEDIA_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/recommendations/summary",
    response_model=RecommendationSummary,
    summary="Executive summary of the recommendation report for an assessment project",
)
def recommendation_summary(assessment_id: int, session: SessionDep):
    report = RecommendationEngine(session).calculate(assessment_id)
    return RecommendationSummary(
        **report.model_dump(exclude={"priority_matrix", "product_comparison", "recommendations"})
    )


@router.get(
    "/recommendations/{assessment_id}",
    response_model=RecommendationReport,
    summary="Get the recommendation report for an assessment project",
)
def get_recommendations(assessment_id: int, session: SessionDep):
    return RecommendationEngine(session).calculate(assessment_id)
