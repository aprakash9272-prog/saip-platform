from typing import Optional

from sqlmodel import Session

from app.models.framework_mapping import FrameworkMapping
from app.repositories.base import BaseRepository


class FrameworkMappingRepository(BaseRepository[FrameworkMapping]):
    search_fields = ("control_id", "control_name")

    def __init__(self, session: Session):
        super().__init__(session, FrameworkMapping)

    def get_by_natural_key(
        self, capability_id: int, framework_id: int, control_id: str
    ) -> Optional[FrameworkMapping]:
        return self.get_by(
            capability_id=capability_id,
            framework_id=framework_id,
            control_id=control_id,
        )
