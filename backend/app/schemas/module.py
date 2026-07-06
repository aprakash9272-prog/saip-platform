from datetime import datetime
from typing import List, Optional

from pydantic import Field
from sqlmodel import SQLModel

from app.models.module import ModuleBase


class ModuleCreate(ModuleBase):
    edition_id: int
    capability_ids: List[int] = Field(default_factory=list)


class ModuleUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    edition_id: Optional[int] = None
    capability_ids: Optional[List[int]] = None


class ModuleRead(ModuleBase):
    id: int
    edition_id: int
    capability_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
