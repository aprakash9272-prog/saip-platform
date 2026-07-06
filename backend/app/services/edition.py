from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.edition import Edition
from app.repositories.edition import EditionRepository
from app.repositories.product import ProductRepository
from app.services.base import BaseService


class EditionService(BaseService[Edition]):
    entity_name = "Edition"

    def __init__(self, session: Session):
        super().__init__(EditionRepository(session))
        self.product_repository = ProductRepository(session)

    def validate_references(self, data: dict) -> None:
        product_id = data.get("product_id")
        if product_id is not None and self.product_repository.get(product_id) is None:
            raise InvalidReferenceError(f"Product with id={product_id} does not exist.")

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        product_id = data.get("product_id")
        name = data.get("name")
        if product_id is None or name is None:
            return
        existing = self.repository.get_by_product_and_name(product_id, name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "Edition", f"product_id={product_id}, name={name!r}"
            )
