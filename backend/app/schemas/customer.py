from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.customer import CustomerBase


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(SQLModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    headquarters: Optional[str] = None


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime
