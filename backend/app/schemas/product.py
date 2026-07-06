from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.product import ProductBase


class ProductCreate(ProductBase):
    vendor_id: int


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    vendor_id: Optional[int] = None


class ProductRead(ProductBase):
    id: int
    vendor_id: int
    created_at: datetime
    updated_at: datetime
