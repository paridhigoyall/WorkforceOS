import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.department import DepartmentResponse

# Basic regex for phone numbers (E.164-ish or optional country code + digits)
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")


class EmployeeBase(BaseModel):
    phone: Optional[str] = Field(
        None,
        description="Contact phone number in E.164 format (e.g. +1234567890)"
    )
    base_salary: Decimal = Field(
        Decimal("0.00"),
        ge=0,
        description="Monthly base salary of the employee"
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        
        # Clean whitespaces, hyphens, and parentheses
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not cleaned:
            return None
            
        if not PHONE_REGEX.match(cleaned):
            raise ValueError("Phone number must be in E.164 format (e.g. +1234567890)")
        
        return cleaned


class EmployeeCreate(EmployeeBase):
    user_id: UUID = Field(..., description="UUID of the associated user account")
    department_id: Optional[UUID] = Field(None, description="UUID of the department")
    hire_date: date = Field(..., description="Hiring date of the employee")

    @field_validator("hire_date")
    @classmethod
    def validate_hire_date(cls, value: date) -> date:
        # Validate that the employee is not hired in the far future
        if value.year > datetime.now().year + 5:
            raise ValueError("Hire date cannot be more than 5 years in the future")
        return value


class EmployeeUpdate(BaseModel):
    department_id: Optional[UUID] = Field(None, description="UUID of the department")
    hire_date: Optional[date] = Field(None, description="Hiring date of the employee")
    phone: Optional[str] = Field(None, description="Contact phone number")
    base_salary: Optional[Decimal] = Field(None, ge=0, description="Monthly base salary")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        return EmployeeBase.validate_phone(value)


class EmployeeResponse(EmployeeBase):
    id: UUID
    user_id: UUID
    department_id: Optional[UUID]
    hire_date: date
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    # Nested relation schemas
    department: Optional[DepartmentResponse] = None

    model_config = ConfigDict(from_attributes=True)
