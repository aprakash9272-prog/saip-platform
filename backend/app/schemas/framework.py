from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.framework import FrameworkBase


class FrameworkCreate(FrameworkBase):
    pass


class FrameworkUpdate(SQLModel):
    name: Optional[str] = None
    version: Optional[str] = None


class FrameworkRead(FrameworkBase):
    id: int
    created_at: datetime
    updated_at: datetime
