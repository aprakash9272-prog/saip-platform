from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.capability import CapabilityBase


class CapabilityCreate(CapabilityBase):
    domain_id: int


class CapabilityUpdate(SQLModel):
    name: Optional[str] = None
    code: Optional[str] = None
    domain_id: Optional[int] = None
    description: Optional[str] = None
    risk_category: Optional[str] = None
    is_business_critical: Optional[bool] = None


class CapabilityRead(CapabilityBase):
    id: int
    domain_id: int
    created_at: datetime
    updated_at: datetime
