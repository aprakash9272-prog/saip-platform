from typing import Optional

from sqlmodel import Session

from app.models.assessment_project import AssessmentProject
from app.repositories.base import BaseRepository


class AssessmentProjectRepository(BaseRepository[AssessmentProject]):
    search_fields = ("name", "description", "status")

    def __init__(self, session: Session):
        super().__init__(session, AssessmentProject)

    def get_by_customer_and_name(
        self, customer_id: int, name: str
    ) -> Optional[AssessmentProject]:
        return self.get_by(customer_id=customer_id, name=name)
