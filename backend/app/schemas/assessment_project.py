from datetime import date, datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import SQLModel

from app.models.assessment_project import AssessmentProjectBase, AssessmentStatus


def _validate_status(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = {item.value for item in AssessmentStatus}
    if value not in allowed:
        raise ValueError(f"status must be one of {sorted(allowed)}")
    return value


class AssessmentProjectCreate(AssessmentProjectBase):
    customer_id: int

    _check_status = field_validator("status")(_validate_status)


class AssessmentProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    target_completion_date: Optional[date] = None
    customer_id: Optional[int] = None

    _check_status = field_validator("status")(_validate_status)


class AssessmentProjectRead(AssessmentProjectBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
