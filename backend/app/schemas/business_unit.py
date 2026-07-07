from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.business_unit import BusinessUnitBase


class BusinessUnitCreate(BusinessUnitBase):
    customer_id: int


class BusinessUnitUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    customer_id: Optional[int] = None


class BusinessUnitRead(BusinessUnitBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
