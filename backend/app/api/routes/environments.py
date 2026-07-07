from typing import Optional

from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationParams, SessionDep
from app.schemas.common import PaginatedResponse
from app.schemas.environment import EnvironmentCreate, EnvironmentRead, EnvironmentUpdate
from app.services.environment import EnvironmentService

router = APIRouter(prefix="/environments", tags=["environments"])


@router.get(
    "", response_model=PaginatedResponse[EnvironmentRead], summary="List environments"
)
def list_environments(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    customer_id: Optional[int] = None,
    environment_type: Optional[str] = None,
):
    service = EnvironmentService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={"customer_id": customer_id, "environment_type": environment_type},
        sort_by=pagination.sort_by,
        sort_desc=pagination.sort_desc,
    )
    return PaginatedResponse[EnvironmentRead](
        items=list(items), total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get(
    "/{item_id}", response_model=EnvironmentRead, summary="Get a single environment"
)
def get_environment(item_id: int, session: SessionDep):
    return EnvironmentService(session).get(item_id)


@router.post(
    "",
    response_model=EnvironmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an environment",
)
def create_environment(payload: EnvironmentCreate, session: SessionDep):
    return EnvironmentService(session).create(payload.model_dump())


@router.put(
    "/{item_id}", response_model=EnvironmentRead, summary="Update an environment"
)
def update_environment(item_id: int, payload: EnvironmentUpdate, session: SessionDep):
    return EnvironmentService(session).update(
        item_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an environment"
)
def delete_environment(item_id: int, session: SessionDep):
    EnvironmentService(session).delete(item_id)
