from typing import Callable, List, Type, TypeVar

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import PaginationParams, SessionDep
from app.schemas.common import PaginatedResponse
from app.services.base import BaseService

ReadT = TypeVar("ReadT", bound=BaseModel)
CreateT = TypeVar("CreateT", bound=BaseModel)
UpdateT = TypeVar("UpdateT", bound=BaseModel)


def build_crud_router(
    *,
    prefix: str,
    tags: List[str],
    service_factory: Callable[[Session], BaseService],
    read_schema: Type[ReadT],
    create_schema: Type[CreateT],
    update_schema: Type[UpdateT],
) -> APIRouter:
    """Build a standard list/get/create/update/delete router for one resource.

    Every knowledge base entity in this sprint (vendors, products, editions,
    capabilities, frameworks, mappings) is a plain SQLModel with no relationship
    fields to project into its read schema, so a single generic router covers
    all of them. Module is the one entity with a many-to-many relationship and
    is wired up with its own router instead.
    """

    resource = prefix.strip("/").replace("/", "_") or "root"
    router = APIRouter(prefix=prefix, tags=tags)

    @router.get(
        "",
        response_model=PaginatedResponse[read_schema],
        operation_id=f"list_{resource}",
        summary=f"List {resource}",
    )
    def list_items(session: SessionDep, pagination: PaginationParams = Depends()):
        service = service_factory(session)
        items, total = service.list(
            skip=pagination.skip,
            limit=pagination.limit,
            search=pagination.search,
            sort_by=pagination.sort_by,
            sort_desc=pagination.sort_desc,
        )
        return PaginatedResponse[read_schema](
            items=list(items),
            total=total,
            skip=pagination.skip,
            limit=pagination.limit,
        )

    @router.get(
        "/{item_id}",
        response_model=read_schema,
        operation_id=f"get_{resource}",
        summary=f"Get a single {resource[:-1] if resource.endswith('s') else resource}",
    )
    def get_item(item_id: int, session: SessionDep):
        service = service_factory(session)
        return service.get(item_id)

    @router.post(
        "",
        response_model=read_schema,
        status_code=status.HTTP_201_CREATED,
        operation_id=f"create_{resource}",
        summary=f"Create a {resource[:-1] if resource.endswith('s') else resource}",
    )
    def create_item(payload: create_schema, session: SessionDep):
        service = service_factory(session)
        return service.create(payload.model_dump())

    @router.put(
        "/{item_id}",
        response_model=read_schema,
        operation_id=f"update_{resource}",
        summary=f"Update a {resource[:-1] if resource.endswith('s') else resource}",
    )
    def update_item(item_id: int, payload: update_schema, session: SessionDep):
        service = service_factory(session)
        return service.update(item_id, payload.model_dump(exclude_unset=True))

    @router.delete(
        "/{item_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        operation_id=f"delete_{resource}",
        summary=f"Delete a {resource[:-1] if resource.endswith('s') else resource}",
    )
    def delete_item(item_id: int, session: SessionDep):
        service = service_factory(session)
        service.delete(item_id)

    return router
