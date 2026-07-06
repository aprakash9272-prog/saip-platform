from typing import Optional

from sqlmodel import Session

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    search_fields = ("name", "category", "description")

    def __init__(self, session: Session):
        super().__init__(session, Product)

    def get_by_vendor_and_name(self, vendor_id: int, name: str) -> Optional[Product]:
        return self.get_by(vendor_id=vendor_id, name=name)
