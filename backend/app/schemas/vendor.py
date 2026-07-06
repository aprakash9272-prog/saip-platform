from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.vendor import VendorBase


class VendorCreate(VendorBase):
    pass


class VendorUpdate(SQLModel):
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    headquarters: Optional[str] = None


class VendorRead(VendorBase):
    id: int
    created_at: datetime
    updated_at: datetime
