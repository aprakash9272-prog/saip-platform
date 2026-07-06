from app.api.routes.factory import build_crud_router
from app.schemas.framework import FrameworkCreate, FrameworkRead, FrameworkUpdate
from app.services.framework import FrameworkService

router = build_crud_router(
    prefix="/frameworks",
    tags=["frameworks"],
    service_factory=FrameworkService,
    read_schema=FrameworkRead,
    create_schema=FrameworkCreate,
    update_schema=FrameworkUpdate,
)
