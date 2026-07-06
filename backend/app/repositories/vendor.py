from typing import Optional

from sqlmodel import Session

from app.models.vendor import Vendor
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    search_fields = ("name", "description", "headquarters")

    def __init__(self, session: Session):
        super().__init__(session, Vendor)

    def get_by_name(self, name: str) -> Optional[Vendor]:
        return self.get_by(name=name)
