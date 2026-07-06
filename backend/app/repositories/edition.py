from typing import Optional

from sqlmodel import Session

from app.models.edition import Edition
from app.repositories.base import BaseRepository


class EditionRepository(BaseRepository[Edition]):
    search_fields = ("name", "tier", "description")

    def __init__(self, session: Session):
        super().__init__(session, Edition)

    def get_by_product_and_name(self, product_id: int, name: str) -> Optional[Edition]:
        return self.get_by(product_id=product_id, name=name)
