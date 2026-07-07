from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class ProductAssignmentExport(BaseModel):
    vendor: str
    product: str
    edition: str
    modules: List[str] = Field(default_factory=list)
    environment: str
    license_quantity: Optional[int] = None
    deployment_model: str
    deployment_status: str
    notes: Optional[str] = None


class AssessmentProjectExport(BaseModel):
    customer: str
    name: str
    description: Optional[str] = None
    status: str
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    assignments: List[ProductAssignmentExport] = Field(default_factory=list)


class AssessmentImportResult(BaseModel):
    project_id: int
    project_status: str
    assignments_created: int = 0
    assignments_updated: int = 0
    assignments_unchanged: int = 0
