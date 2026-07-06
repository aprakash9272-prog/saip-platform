from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.edition import EditionBase


class EditionCreate(EditionBase):
    product_id: int


class EditionUpdate(SQLModel):
    name: Optional[str] = None
    tier: Optional[str] = None
    description: Optional[str] = None
    product_id: Optional[int] = None


class EditionRead(EditionBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime
