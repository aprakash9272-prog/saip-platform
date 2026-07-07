from typing import List, Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.module import Module
from app.models.product_assignment import ProductAssignment
from app.repositories.assessment_project import AssessmentProjectRepository
from app.repositories.edition import EditionRepository
from app.repositories.environment import EnvironmentRepository
from app.repositories.module import ModuleRepository
from app.repositories.product import ProductRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.repositories.vendor import VendorRepository
from app.services.base import BaseService


class ProductAssignmentService(BaseService[ProductAssignment]):
    entity_name = "ProductAssignment"

    def __init__(self, session: Session):
        super().__init__(ProductAssignmentRepository(session))
        self.session = session
        self.assessment_project_repository = AssessmentProjectRepository(session)
        self.vendor_repository = VendorRepository(session)
        self.product_repository = ProductRepository(session)
        self.edition_repository = EditionRepository(session)
        self.environment_repository = EnvironmentRepository(session)
        self.module_repository = ModuleRepository(session)

    def validate_references(self, data: dict) -> None:
        assessment_project_id = data.get("assessment_project_id")
        vendor_id = data.get("vendor_id")
        product_id = data.get("product_id")
        edition_id = data.get("edition_id")
        environment_id = data.get("environment_id")

        assessment_project = (
            self.assessment_project_repository.get(assessment_project_id)
            if assessment_project_id is not None
            else None
        )
        if assessment_project_id is not None and assessment_project is None:
            raise InvalidReferenceError(
                f"AssessmentProject with id={assessment_project_id} does not exist."
            )

        vendor = self.vendor_repository.get(vendor_id) if vendor_id is not None else None
        if vendor_id is not None and vendor is None:
            raise InvalidReferenceError(f"Vendor with id={vendor_id} does not exist.")

        product = (
            self.product_repository.get(product_id) if product_id is not None else None
        )
        if product_id is not None and product is None:
            raise InvalidReferenceError(f"Product with id={product_id} does not exist.")
        if product is not None and vendor is not None and product.vendor_id != vendor.id:
            raise InvalidReferenceError(
                f"Product {product_id} does not belong to vendor {vendor_id}."
            )

        edition = (
            self.edition_repository.get(edition_id) if edition_id is not None else None
        )
        if edition_id is not None and edition is None:
            raise InvalidReferenceError(f"Edition with id={edition_id} does not exist.")
        if edition is not None and product is not None and edition.product_id != product.id:
            raise InvalidReferenceError(
                f"Edition {edition_id} does not belong to product {product_id}."
            )

        environment = (
            self.environment_repository.get(environment_id)
            if environment_id is not None
            else None
        )
        if environment_id is not None and environment is None:
            raise InvalidReferenceError(
                f"Environment with id={environment_id} does not exist."
            )
        if (
            environment is not None
            and assessment_project is not None
            and environment.customer_id != assessment_project.customer_id
        ):
            raise InvalidReferenceError(
                f"Environment {environment_id} does not belong to the same "
                f"customer as assessment project {assessment_project_id}."
            )

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        assessment_project_id = data.get("assessment_project_id")
        edition_id = data.get("edition_id")
        environment_id = data.get("environment_id")
        if assessment_project_id is None or edition_id is None or environment_id is None:
            return
        existing = self.repository.get_by_natural_key(
            assessment_project_id, edition_id, environment_id
        )
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "ProductAssignment",
                f"assessment_project_id={assessment_project_id}, "
                f"edition_id={edition_id}, environment_id={environment_id}",
            )

    def _resolve_modules(self, module_ids: List[int], edition_id: Optional[int]) -> List[Module]:
        modules = []
        for module_id in module_ids:
            module = self.module_repository.get(module_id)
            if module is None:
                raise InvalidReferenceError(f"Module with id={module_id} does not exist.")
            if edition_id is not None and module.edition_id != edition_id:
                raise InvalidReferenceError(
                    f"Module {module_id} does not belong to edition {edition_id}."
                )
            modules.append(module)
        return modules

    def create(self, data: dict) -> ProductAssignment:
        data = dict(data)
        module_ids = data.pop("module_ids", [])
        self.validate_references(data)
        self.validate_duplicate(data)
        modules = self._resolve_modules(module_ids, data.get("edition_id"))
        obj = ProductAssignment(**data)
        obj.modules = modules
        return self.repository.create(obj)

    def update(self, id_: int, data: dict) -> ProductAssignment:
        obj = self.get(id_)
        data = dict(data)
        module_ids = data.pop("module_ids", None)
        clean = {k: v for k, v in data.items() if v is not None}
        self.validate_references(clean)
        self.validate_duplicate(clean, exclude_id=id_)
        updated = self.repository.update(obj, clean)
        if module_ids is not None:
            edition_id = clean.get("edition_id", updated.edition_id)
            updated.modules = self._resolve_modules(module_ids, edition_id)
            self.session.add(updated)
            self.session.commit()
            self.session.refresh(updated)
        return updated
