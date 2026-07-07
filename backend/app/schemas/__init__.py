from app.schemas.assessment_export import (
    AssessmentImportResult,
    AssessmentProjectExport,
    ProductAssignmentExport,
)
from app.schemas.assessment_project import (
    AssessmentProjectCreate,
    AssessmentProjectRead,
    AssessmentProjectUpdate,
)
from app.schemas.business_unit import (
    BusinessUnitCreate,
    BusinessUnitRead,
    BusinessUnitUpdate,
)
from app.schemas.capability import CapabilityCreate, CapabilityRead, CapabilityUpdate
from app.schemas.common import PaginatedResponse
from app.schemas.coverage import (
    CapabilityCoverageItem,
    CapabilityMatrix,
    CoverageReport,
    CoverageRequest,
    DomainCoverage,
    DuplicateCapabilityItem,
)
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.schemas.dashboard import AssessmentDashboard
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate
from app.schemas.edition import EditionCreate, EditionRead, EditionUpdate
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentRead,
    EnvironmentUpdate,
)
from app.schemas.framework import FrameworkCreate, FrameworkRead, FrameworkUpdate
from app.schemas.framework_mapping import (
    FrameworkMappingCreate,
    FrameworkMappingRead,
    FrameworkMappingUpdate,
)
from app.schemas.gap import (
    DomainGapScore,
    FrameworkControlRef,
    GapItem,
    GapReport,
    GapRequest,
    GapSummary,
)
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate
from app.schemas.overlap import (
    DomainOverlapScore,
    DuplicateCapabilityOverlap,
    FrameworkOverlapItem,
    ModuleOverlapPair,
    OverlapReport,
    OverlapRequest,
    OverlapSummary,
    ProductOverlapPair,
    RedundantLicenseItem,
    UnusedCapabilityItem,
    VendorOverlapSummary,
)
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.schemas.product_assignment import (
    ProductAssignmentCreate,
    ProductAssignmentRead,
    ProductAssignmentUpdate,
)
from app.schemas.product_capability_mapping import (
    BulkOperationResult,
    ProductCapabilityMappingBulkDelete,
    ProductCapabilityMappingBulkUpdate,
    ProductCapabilityMappingCreate,
    ProductCapabilityMappingRead,
    ProductCapabilityMappingUpdate,
)
from app.schemas.recommendation import (
    CoverageForecast,
    PriorityBreakdown,
    ProductCandidate,
    ProductComparisonEntry,
    RecommendationItem,
    RecommendationReport,
    RecommendationRequest,
    RecommendationSummary,
)
from app.schemas.vendor import VendorCreate, VendorRead, VendorUpdate

__all__ = [
    "PaginatedResponse",
    "VendorCreate",
    "VendorRead",
    "VendorUpdate",
    "ProductCreate",
    "ProductRead",
    "ProductUpdate",
    "EditionCreate",
    "EditionRead",
    "EditionUpdate",
    "ModuleCreate",
    "ModuleRead",
    "ModuleUpdate",
    "DomainCreate",
    "DomainRead",
    "DomainUpdate",
    "CapabilityCreate",
    "CapabilityRead",
    "CapabilityUpdate",
    "FrameworkCreate",
    "FrameworkRead",
    "FrameworkUpdate",
    "FrameworkMappingCreate",
    "FrameworkMappingRead",
    "FrameworkMappingUpdate",
    "ProductCapabilityMappingCreate",
    "ProductCapabilityMappingRead",
    "ProductCapabilityMappingUpdate",
    "ProductCapabilityMappingBulkUpdate",
    "ProductCapabilityMappingBulkDelete",
    "BulkOperationResult",
    "CustomerCreate",
    "CustomerRead",
    "CustomerUpdate",
    "BusinessUnitCreate",
    "BusinessUnitRead",
    "BusinessUnitUpdate",
    "EnvironmentCreate",
    "EnvironmentRead",
    "EnvironmentUpdate",
    "AssessmentProjectCreate",
    "AssessmentProjectRead",
    "AssessmentProjectUpdate",
    "ProductAssignmentCreate",
    "ProductAssignmentRead",
    "ProductAssignmentUpdate",
    "AssessmentDashboard",
    "AssessmentProjectExport",
    "ProductAssignmentExport",
    "AssessmentImportResult",
    "CoverageRequest",
    "CoverageReport",
    "CapabilityCoverageItem",
    "DuplicateCapabilityItem",
    "DomainCoverage",
    "CapabilityMatrix",
    "GapRequest",
    "GapItem",
    "FrameworkControlRef",
    "DomainGapScore",
    "GapSummary",
    "GapReport",
    "RecommendationRequest",
    "ProductCandidate",
    "RecommendationItem",
    "PriorityBreakdown",
    "ProductComparisonEntry",
    "CoverageForecast",
    "RecommendationSummary",
    "RecommendationReport",
    "OverlapRequest",
    "DuplicateCapabilityOverlap",
    "ProductOverlapPair",
    "ModuleOverlapPair",
    "FrameworkOverlapItem",
    "RedundantLicenseItem",
    "UnusedCapabilityItem",
    "VendorOverlapSummary",
    "DomainOverlapScore",
    "OverlapSummary",
    "OverlapReport",
]
