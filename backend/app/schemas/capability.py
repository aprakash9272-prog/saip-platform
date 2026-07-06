from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.capability import CapabilityBase


class CapabilityCreate(CapabilityBase):
    pass


class CapabilityUpdate(SQLModel):
    name: Optional[str] = None
    code: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    risk_category: Optional[str] = None


class CapabilityRead(CapabilityBase):
    id: int
    created_at: datetime
    updated_at: datetime
