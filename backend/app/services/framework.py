from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError
from app.models.framework import Framework
from app.repositories.framework import FrameworkRepository
from app.services.base import BaseService


class FrameworkService(BaseService[Framework]):
    entity_name = "Framework"

    def __init__(self, session: Session):
        super().__init__(FrameworkRepository(session))

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        name = data.get("name")
        version = data.get("version")
        if name is None or version is None:
            return
        existing = self.repository.get_by_name_version(name, version)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "Framework", f"name={name!r}, version={version!r}"
            )
