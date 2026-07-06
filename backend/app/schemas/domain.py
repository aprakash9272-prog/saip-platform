from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.domain import DomainBase


class DomainCreate(DomainBase):
    pass


class DomainUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DomainRead(DomainBase):
    id: int
    created_at: datetime
    updated_at: datetime
