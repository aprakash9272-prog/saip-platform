import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    assessment_projects,
    business_units,
    capabilities,
    customers,
    domains,
    editions,
    environments,
    frameworks,
    health,
    mappings,
    modules,
    product_assignments,
    product_mappings,
    products,
    vendors,
)
from app.core.config import settings
from app.core.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    InvalidReferenceError,
)
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Security Architecture Intelligence Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(EntityNotFoundError)
def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(DuplicateEntityError)
def duplicate_entity_handler(request: Request, exc: DuplicateEntityError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.exception_handler(InvalidReferenceError)
def invalid_reference_handler(
    request: Request, exc: InvalidReferenceError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": str(exc)}
    )


app.include_router(health.router)
app.include_router(vendors.router)
app.include_router(products.router)
app.include_router(editions.router)
app.include_router(modules.router)
app.include_router(domains.router)
app.include_router(capabilities.router)
app.include_router(frameworks.router)
app.include_router(mappings.router)
app.include_router(product_mappings.router)
app.include_router(customers.router)
app.include_router(business_units.router)
app.include_router(environments.router)
app.include_router(assessment_projects.router)
app.include_router(product_assignments.router)


@app.on_event("startup")
def on_startup() -> None:
    logger.info("%s starting up in %s mode", settings.APP_NAME, settings.ENVIRONMENT)
