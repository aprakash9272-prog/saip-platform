from typing import List, Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.product_capability_mapping import ProductCapabilityMapping
from app.repositories.capability import CapabilityRepository
from app.repositories.edition import EditionRepository
from app.repositories.module import ModuleRepository
from app.repositories.product import ProductRepository
from app.repositories.product_capability_mapping import ProductCapabilityMappingRepository
from app.repositories.vendor import VendorRepository
from app.services.base import BaseService


class ProductCapabilityMappingService(BaseService[ProductCapabilityMapping]):
    entity_name = "ProductCapabilityMapping"

    def __init__(self, session: Session):
        super().__init__(ProductCapabilityMappingRepository(session))
        self.session = session
        self.vendor_repository = VendorRepository(session)
        self.product_repository = ProductRepository(session)
        self.edition_repository = EditionRepository(session)
        self.module_repository = ModuleRepository(session)
        self.capability_repository = CapabilityRepository(session)

    def validate_references(self, data: dict) -> None:
        vendor_id = data.get("vendor_id")
        product_id = data.get("product_id")
        edition_id = data.get("edition_id")
        module_id = data.get("module_id")
        capability_id = data.get("capability_id")

        vendor = self.vendor_repository.get(vendor_id) if vendor_id is not None else None
        if vendor_id is not None and vendor is None:
            raise InvalidReferenceError(f"Vendor with id={vendor_id} does not exist.")

        product = self.product_repository.get(product_id) if product_id is not None else None
        if product_id is not None and product is None:
            raise InvalidReferenceError(f"Product with id={product_id} does not exist.")
        if product is not None and vendor is not None and product.vendor_id != vendor.id:
            raise InvalidReferenceError(
                f"Product {product_id} does not belong to vendor {vendor_id}."
            )

        edition = self.edition_repository.get(edition_id) if edition_id is not None else None
        if edition_id is not None and edition is None:
            raise InvalidReferenceError(f"Edition with id={edition_id} does not exist.")
        if edition is not None and product is not None and edition.product_id != product.id:
            raise InvalidReferenceError(
                f"Edition {edition_id} does not belong to product {product_id}."
            )

        module = self.module_repository.get(module_id) if module_id is not None else None
        if module_id is not None and module is None:
            raise InvalidReferenceError(f"Module with id={module_id} does not exist.")
        if module is not None and edition is not None and module.edition_id != edition.id:
            raise InvalidReferenceError(
                f"Module {module_id} does not belong to edition {edition_id}."
            )

        if (
            capability_id is not None
            and self.capability_repository.get(capability_id) is None
        ):
            raise InvalidReferenceError(
                f"Capability with id={capability_id} does not exist."
            )

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        module_id = data.get("module_id")
        capability_id = data.get("capability_id")
        deployment_model = data.get("deployment_model")
        if module_id is None or capability_id is None or deployment_model is None:
            return
        licensing_tier = data.get("licensing_tier")
        existing = self.repository.get_by_natural_key(
            module_id, capability_id, licensing_tier, deployment_model
        )
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "ProductCapabilityMapping",
                f"module_id={module_id}, capability_id={capability_id}, "
                f"licensing_tier={licensing_tier!r}, deployment_model={deployment_model!r}",
            )

    def bulk_update(self, ids: List[int], patch: dict) -> tuple[int, List[str]]:
        clean = {k: v for k, v in patch.items() if v is not None}
        updated = 0
        failed: List[str] = []
        for id_ in ids:
            obj = self.repository.get(id_)
            if obj is None:
                failed.append(f"id={id_}: not found")
                continue
            merged = {
                "vendor_id": obj.vendor_id,
                "product_id": obj.product_id,
                "edition_id": obj.edition_id,
                "module_id": obj.module_id,
                "capability_id": obj.capability_id,
                "licensing_tier": obj.licensing_tier,
                "deployment_model": obj.deployment_model,
                **clean,
            }
            try:
                self.validate_references(merged)
                self.validate_duplicate(merged, exclude_id=id_)
            except InvalidReferenceError as exc:
                failed.append(f"id={id_}: {exc}")
                continue
            except DuplicateEntityError as exc:
                failed.append(f"id={id_}: {exc}")
                continue
            self.repository.update(obj, clean)
            updated += 1
        return updated, failed

    def bulk_delete(self, ids: List[int]) -> tuple[int, List[str]]:
        deleted = 0
        failed: List[str] = []
        for id_ in ids:
            obj = self.repository.get(id_)
            if obj is None:
                failed.append(f"id={id_}: not found")
                continue
            self.repository.delete(obj)
            deleted += 1
        return deleted, failed

    def list_facets(self) -> dict:
        return {
            "deployment_models": self.repository.list_deployment_models(),
            "availability_statuses": self.repository.list_availability_statuses(),
            "licensing_tiers": self.repository.list_licensing_tiers(),
        }

    def export_all(self) -> List[ProductCapabilityMapping]:
        return self.repository.all()
