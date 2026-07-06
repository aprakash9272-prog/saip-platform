from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.models.framework_mapping import FrameworkMappingBase


class FrameworkMappingCreate(FrameworkMappingBase):
    capability_id: int
    framework_id: int


class FrameworkMappingUpdate(SQLModel):
    control_id: Optional[str] = None
    control_name: Optional[str] = None
    capability_id: Optional[int] = None
    framework_id: Optional[int] = None


class FrameworkMappingRead(FrameworkMappingBase):
    id: int
    capability_id: int
    framework_id: int
    created_at: datetime
    updated_at: datetime
