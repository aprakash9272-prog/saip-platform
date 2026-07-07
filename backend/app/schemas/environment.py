from datetime import datetime
from typing import Optional

from pydantic import field_validator
from sqlmodel import SQLModel

from app.models.environment import EnvironmentBase, EnvironmentType


def _validate_environment_type(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    allowed = {item.value for item in EnvironmentType}
    if value not in allowed:
        raise ValueError(f"environment_type must be one of {sorted(allowed)}")
    return value


class EnvironmentCreate(EnvironmentBase):
    customer_id: int

    _check_environment_type = field_validator("environment_type")(
        _validate_environment_type
    )


class EnvironmentUpdate(SQLModel):
    name: Optional[str] = None
    environment_type: Optional[str] = None
    description: Optional[str] = None
    customer_id: Optional[int] = None

    _check_environment_type = field_validator("environment_type")(
        _validate_environment_type
    )


class EnvironmentRead(EnvironmentBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime
