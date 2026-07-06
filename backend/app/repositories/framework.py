from typing import Optional

from sqlmodel import Session

from app.models.framework import Framework
from app.repositories.base import BaseRepository


class FrameworkRepository(BaseRepository[Framework]):
    search_fields = ("name", "version")

    def __init__(self, session: Session):
        super().__init__(session, Framework)

    def get_by_name_version(self, name: str, version: str) -> Optional[Framework]:
        return self.get_by(name=name, version=version)
