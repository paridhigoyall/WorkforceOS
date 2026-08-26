from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AttendanceInsights(BaseModel):
    total_records: int = Field(..., description="Total attendance records checked")
    average_attendance_rate: float = Field(..., description="Percentage of active workdays checked in")
    late_check_ins: int = Field(..., description="Count of late check-ins")
    late_rate: float = Field(..., description="Percentage of check-ins marked as LATE")
    total_overtime_hours: float = Field(..., description="Total hours worked beyond regular shift hours")
    total_under_hours: float = Field(..., description="Total hours missed below regular shift hours")
    average_daily_hours: float = Field(..., description="Average hours worked per check-in")


class LeaveInsights(BaseModel):
    total_requests: int = Field(..., description="Total leave requests submitted")
    approved_requests: int = Field(..., description="Count of approved leave requests")
    pending_requests: int = Field(..., description="Count of pending leave requests")
    rejected_requests: int = Field(..., description="Count of rejected leave requests")
    cancelled_requests: int = Field(..., description="Count of cancelled leave requests")
    total_days_taken: int = Field(..., description="Total days of approved leaves taken")
    days_taken_by_type: Dict[str, int] = Field(..., description="Breakdown of leave days by leave type")
    utilization_rate: float = Field(..., description="Percentage of allocated leave balance utilized")


class DepartmentInsights(BaseModel):
    department_id: UUID
    department_name: str
    headcount: int = Field(..., description="Number of employees in the department")
    total_monthly_payroll: Decimal = Field(..., description="Sum of monthly salaries of the department")
    average_salary: Decimal = Field(..., description="Average salary in the department")
    average_attendance_rate: float = Field(..., description="Average attendance rate of department employees")
    average_overtime_hours: float = Field(..., description="Average overtime hours per employee in the department")


class AIPredictionDatasetRow(BaseModel):
    employee_id: UUID
    tenure_days: int = Field(..., description="Number of days since employee hire date")
    base_salary: Decimal = Field(..., description="Monthly base salary")
    attendance_rate: float = Field(..., description="Historical attendance rate")
    late_rate: float = Field(..., description="Percentage of check-ins that were late")
    total_overtime_hours: float = Field(..., description="Total overtime hours accumulated")
    leave_requests_count: int = Field(..., description="Total leave requests filed")
    leave_days_taken: int = Field(..., description="Total leave days taken")
    anomaly_flags_count: int = Field(..., description="Number of flagged check-in anomalies")
    turnover_risk_label: int = Field(..., description="Engine-calculated potential turnover risk category (0: Low, 1: Medium, 2: High)")


class AIPredictionDataset(BaseModel):
    generated_at: datetime
    data: List[AIPredictionDatasetRow]

    model_config = ConfigDict(from_attributes=True)


class EmployeeTurnoverRiskDetail(BaseModel):
    employee_id: UUID
    employee_email: Optional[str] = None
    department_name: Optional[str] = None
    risk_score: float = Field(..., description="Calculated flight risk percentage from 0 to 100")
    risk_level: str = Field(..., description="Risk tier: LOW, MEDIUM, HIGH, or CRITICAL")
    tenure_days: int
    attendance_rate: float
    late_rate: float
    overtime_hours: float
    leave_requests_count: int
    primary_risk_drivers: List[str] = Field(default_factory=list, description="Specific indicators causing risk score elevations")
    recommended_interventions: List[str] = Field(default_factory=list, description="Actionable retention recommendations for HR")


class TurnoverRiskOverview(BaseModel):
    total_evaluated: int
    low_risk_count: int
    medium_risk_count: int
    high_risk_count: int
    critical_risk_count: int
    average_workforce_risk_score: float
    highest_risk_employees: List[EmployeeTurnoverRiskDetail]
    department_risk_summary: Dict[str, float]

