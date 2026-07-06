from app.api.routes.factory import build_crud_router
from app.schemas.edition import EditionCreate, EditionRead, EditionUpdate
from app.services.edition import EditionService

router = build_crud_router(
    prefix="/editions",
    tags=["editions"],
    service_factory=EditionService,
    read_schema=EditionRead,
    create_schema=EditionCreate,
    update_schema=EditionUpdate,
)
