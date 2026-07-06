from app.api.routes.factory import build_crud_router
from app.schemas.framework_mapping import (
    FrameworkMappingCreate,
    FrameworkMappingRead,
    FrameworkMappingUpdate,
)
from app.services.framework_mapping import FrameworkMappingService

router = build_crud_router(
    prefix="/mappings",
    tags=["mappings"],
    service_factory=FrameworkMappingService,
    read_schema=FrameworkMappingRead,
    create_schema=FrameworkMappingCreate,
    update_schema=FrameworkMappingUpdate,
)
