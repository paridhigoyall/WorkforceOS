from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.payroll import PayrollPeriodStatus, PayrollRecordStatus


class PayrollGenerationRequest(BaseModel):
    """Payload for generating monthly payroll."""
    year: int = Field(..., ge=2000, le=2100, description="Calendar year")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")


class PayrollRecordResponse(BaseModel):
    """Detailed employee payslip record response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    payroll_period_id: UUID
    employee_id: UUID
    employee_email: Optional[str] = None
    department_name: Optional[str] = None
    base_salary: float
    overtime_hours: float
    overtime_pay: float
    unpaid_leave_days: int
    unpaid_leave_deduction: float
    tax_deduction: float
    net_pay: float
    status: PayrollRecordStatus
    created_at: datetime


class PayrollPeriodResponse(BaseModel):
    """Payroll batch period summary response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    year: int
    month: int
    status: PayrollPeriodStatus
    total_gross_pay: float
    total_deductions: float
    total_net_pay: float
    employee_count: int
    approved_at: Optional[datetime] = None
    created_at: datetime
    records: Optional[List[PayrollRecordResponse]] = None


class PayslipDetailResponse(BaseModel):
    """Comprehensive printable digital payslip."""
    id: UUID
    period_year: int
    period_month: int
    employee_id: UUID
    employee_email: Optional[str] = None
    department_name: Optional[str] = None
    base_salary: float
    overtime_hours: float
    overtime_pay: float
    unpaid_leave_days: int
    unpaid_leave_deduction: float
    gross_earnings: float
    total_deductions: float
    tax_deduction: float
    net_pay: float
    status: PayrollRecordStatus
    generated_at: datetime
