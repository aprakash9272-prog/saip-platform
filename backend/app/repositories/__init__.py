from app.repositories.capability import CapabilityRepository
from app.repositories.domain import DomainRepository
from app.repositories.edition import EditionRepository
from app.repositories.framework import FrameworkRepository
from app.repositories.framework_mapping import FrameworkMappingRepository
from app.repositories.module import ModuleRepository
from app.repositories.product import ProductRepository
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
]
