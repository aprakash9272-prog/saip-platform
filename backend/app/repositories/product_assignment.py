from typing import List, Optional

from sqlmodel import Session

from app.models.product_assignment import ProductAssignment
from app.repositories.base import BaseRepository


class ProductAssignmentRepository(BaseRepository[ProductAssignment]):
    search_fields = ("notes", "deployment_model", "deployment_status")

    def __init__(self, session: Session):
        super().__init__(session, ProductAssignment)

    def get_by_natural_key(
        self, assessment_project_id: int, edition_id: int, environment_id: int
    ) -> Optional[ProductAssignment]:
        return self.get_by(
            assessment_project_id=assessment_project_id,
            edition_id=edition_id,
            environment_id=environment_id,
        )

    def list_by_assessment_project(
        self, assessment_project_id: int
    ) -> List[ProductAssignment]:
        items, _ = self.list(
            skip=0, limit=1_000_000, filters={"assessment_project_id": assessment_project_id}
        )
        return items
