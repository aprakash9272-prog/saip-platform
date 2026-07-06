from typing import Optional

from sqlmodel import Session

from app.models.module import Module
from app.repositories.base import BaseRepository


class ModuleRepository(BaseRepository[Module]):
    search_fields = ("name", "description")

    def __init__(self, session: Session):
        super().__init__(session, Module)

    def get_by_edition_and_name(self, edition_id: int, name: str) -> Optional[Module]:
        return self.get_by(edition_id=edition_id, name=name)
