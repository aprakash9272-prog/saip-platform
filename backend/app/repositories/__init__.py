from app.repositories.assessment_project import AssessmentProjectRepository
from app.repositories.business_unit import BusinessUnitRepository
from app.repositories.capability import CapabilityRepository
from app.repositories.customer import CustomerRepository
from app.repositories.domain import DomainRepository
from app.repositories.edition import EditionRepository
from app.repositories.environment import EnvironmentRepository
from app.repositories.framework import FrameworkRepository
from app.repositories.framework_mapping import FrameworkMappingRepository
from app.repositories.module import ModuleRepository
from app.repositories.product import ProductRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.repositories.product_capability_mapping import ProductCapabilityMappingRepository
from app.repositories.vendor import VendorRepository

__all__ = [
    "VendorRepository",
    "ProductRepository",
    "EditionRepository",
    "ModuleRepository",
    "DomainRepository",
    "CapabilityRepository",
    "FrameworkRepository",
    "FrameworkMappingRepository",
    "ProductCapabilityMappingRepository",
    "CustomerRepository",
    "BusinessUnitRepository",
    "EnvironmentRepository",
    "AssessmentProjectRepository",
    "ProductAssignmentRepository",
]
