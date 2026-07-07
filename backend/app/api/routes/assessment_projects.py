from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import PaginationParams, SessionDep
from app.core.exceptions import InvalidReferenceError
from app.schemas.assessment_export import AssessmentImportResult, AssessmentProjectExport
from app.schemas.assessment_project import (
    AssessmentProjectCreate,
    AssessmentProjectRead,
    AssessmentProjectUpdate,
)
from app.schemas.common import PaginatedResponse
from app.schemas.dashboard import AssessmentDashboard
from app.services.assessment_project import AssessmentProjectService

router = APIRouter(prefix="/assessment-projects", tags=["assessment-projects"])


@router.get(
    "",
    response_model=PaginatedResponse[AssessmentProjectRead],
    summary="List assessment projects",
)
def list_assessment_projects(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    customer_id: Optional[int] = None,
    status_: Optional[str] = Query(default=None, alias="status"),
):
    service = AssessmentProjectService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={"customer_id": customer_id, "status": status_},
        sort_by=pagination.sort_by,
        sort_desc=pagination.sort_desc,
    )
    return PaginatedResponse[AssessmentProjectRead](
        items=list(items), total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.post(
    "/import",
    response_model=AssessmentImportResult,
    summary="Import an assessment project (and its product assignments) from JSON",
)
def import_assessment_project(payload: AssessmentProjectExport, session: SessionDep):
    """Idempotent upsert: re-importing the same export reports assignments as
    unchanged. The referenced customer, and every vendor/product/edition/
    module/environment referenced by an assignment, must already exist."""
    service = AssessmentProjectService(session)
    try:
        return service.import_payload(payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc


@router.get(
    "/{item_id}", response_model=AssessmentProjectRead, summary="Get a single assessment project"
)
def get_assessment_project(item_id: int, session: SessionDep):
    return AssessmentProjectService(session).get(item_id)


@router.get(
    "/{item_id}/dashboard",
    response_model=AssessmentDashboard,
    summary="Informational rollup of an assessment project's deployed products",
)
def get_assessment_project_dashboard(item_id: int, session: SessionDep):
    return AssessmentProjectService(session).dashboard(item_id)


@router.get(
    "/{item_id}/export",
    response_model=AssessmentProjectExport,
    summary="Export an assessment project and its product assignments as JSON",
)
def export_assessment_project(item_id: int, session: SessionDep):
    return AssessmentProjectService(session).export(item_id)


@router.post(
    "",
    response_model=AssessmentProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an assessment project",
)
def create_assessment_project(payload: AssessmentProjectCreate, session: SessionDep):
    return AssessmentProjectService(session).create(payload.model_dump())


@router.put(
    "/{item_id}",
    response_model=AssessmentProjectRead,
    summary="Update an assessment project",
)
def update_assessment_project(
    item_id: int, payload: AssessmentProjectUpdate, session: SessionDep
):
    return AssessmentProjectService(session).update(
        item_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assessment project",
)
def delete_assessment_project(item_id: int, session: SessionDep):
    AssessmentProjectService(session).delete(item_id)
