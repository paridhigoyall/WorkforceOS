from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DepartmentBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="The unique name of the department"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="A brief description of the department's purpose"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Department name cannot be empty or whitespace only")
        return stripped


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="The unique name of the department"
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="A brief description of the department's purpose"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("Department name cannot be empty or whitespace only")
        return stripped


class DepartmentResponse(DepartmentBase):
    id: UUID
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
