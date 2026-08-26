from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance, AttendanceStatus
from app.models.leave import LeaveRequest, LeaveBalance, LeaveStatus, LeaveType
from app.models.audit_log import AuditLog
from app.schemas.insights import (
    AttendanceInsights,
    LeaveInsights,
    DepartmentInsights,
    AIPredictionDataset,
    AIPredictionDatasetRow,
    TurnoverRiskOverview,
    EmployeeTurnoverRiskDetail,
)



class InsightsService:
    """Service layer to compute analytics and workforce insights."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def get_attendance_insights(self, employee_id: Optional[UUID] = None) -> AttendanceInsights:
        """Calculate and return key attendance statistics."""
        stmt = select(Attendance)
        if employee_id:
            stmt = stmt.where(Attendance.employee_id == employee_id)
        
        result = await self.db_session.execute(stmt)
        records = result.scalars().all()
        
        total_records = len(records)
        if total_records == 0:
            return AttendanceInsights(
                total_records=0,
                average_attendance_rate=0.0,
                late_check_ins=0,
                late_rate=0.0,
                total_overtime_hours=0.0,
                total_under_hours=0.0,
                average_daily_hours=0.0,
            )

        present_or_late = sum(
            1 for r in records if r.attendance_status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE)
        )
        late_count = sum(1 for r in records if r.attendance_status == AttendanceStatus.LATE)
        
        total_hours = sum(r.total_hours for r in records)
        total_overtime = sum(max(Decimal("0.00"), r.total_hours - Decimal("8.00")) for r in records)
        total_under = sum(max(Decimal("0.00"), Decimal("8.00") - r.total_hours) for r in records)

        return AttendanceInsights(
            total_records=total_records,
            average_attendance_rate=float((present_or_late / total_records) * 100.0),
            late_check_ins=late_count,
            late_rate=float((late_count / total_records) * 100.0),
            total_overtime_hours=float(total_overtime),
            total_under_hours=float(total_under),
            average_daily_hours=float(total_hours / total_records),
        )

    async def get_leave_insights(self, employee_id: Optional[UUID] = None) -> LeaveInsights:
        """Calculate and return leave metrics and utilization rates."""
        # 1. Gather all leave requests
        req_stmt = select(LeaveRequest)
        if employee_id:
            req_stmt = req_stmt.where(LeaveRequest.employee_id == employee_id)
        
        req_res = await self.db_session.execute(req_stmt)
        requests = req_res.scalars().all()
        
        total_requests = len(requests)
        approved_requests = sum(1 for r in requests if r.status == LeaveStatus.APPROVED)
        pending_requests = sum(1 for r in requests if r.status == LeaveStatus.PENDING)
        rejected_requests = sum(1 for r in requests if r.status == LeaveStatus.REJECTED)
        cancelled_requests = sum(1 for r in requests if r.status == LeaveStatus.CANCELLED)
        
        total_days_taken = sum(r.total_days for r in requests if r.status == LeaveStatus.APPROVED)
        
        days_taken_by_type: Dict[str, int] = {}
        for lt in LeaveType:
            days_taken_by_type[lt.value] = sum(
                r.total_days for r in requests if r.status == LeaveStatus.APPROVED and r.leave_type == lt
            )

        # 2. Calculate leave balance utilization
        bal_stmt = select(LeaveBalance)
        if employee_id:
            bal_stmt = bal_stmt.where(LeaveBalance.employee_id == employee_id)
            
        bal_res = await self.db_session.execute(bal_stmt)
        balances = bal_res.scalars().all()
        
        total_allocated = sum(b.allocated_days for b in balances)
        total_used = sum(b.used_days for b in balances)
        
        utilization_rate = 0.0
        if total_allocated > 0:
            utilization_rate = float((total_used / total_allocated) * 100.0)

        return LeaveInsights(
            total_requests=total_requests,
            approved_requests=approved_requests,
            pending_requests=pending_requests,
            rejected_requests=rejected_requests,
            cancelled_requests=cancelled_requests,
            total_days_taken=total_days_taken,
            days_taken_by_type=days_taken_by_type,
            utilization_rate=utilization_rate,
        )

    async def get_department_insights(self) -> List[DepartmentInsights]:
        """Aggregate insights per department."""
        stmt = select(Department).options(selectinload(Department.employees))
        result = await self.db_session.execute(stmt)
        departments = result.scalars().all()
        
        insights_list = []
        for dept in departments:
            active_employees = [e for e in dept.employees if not e.is_deleted]
            headcount = len(active_employees)
            if headcount == 0:
                insights_list.append(
                    DepartmentInsights(
                        department_id=dept.id,
                        department_name=dept.name,
                        headcount=0,
                        total_monthly_payroll=Decimal("0.00"),
                        average_salary=Decimal("0.00"),
                        average_attendance_rate=0.0,
                        average_overtime_hours=0.0,
                    )
                )
                continue
            
            total_payroll = sum(e.base_salary for e in active_employees)
            avg_salary = total_payroll / headcount
            
            # Compute attendance & overtime metrics for all employees in this department
            emp_ids = [e.id for e in active_employees]
            att_stmt = select(Attendance).where(Attendance.employee_id.in_(emp_ids))
            att_res = await self.db_session.execute(att_stmt)
            attendances = att_res.scalars().all()
            
            avg_att_rate = 0.0
            avg_ot_hours = 0.0
            
            if len(attendances) > 0:
                present_or_late = sum(
                    1 for r in attendances if r.attendance_status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE)
                )
                avg_att_rate = (present_or_late / len(attendances)) * 100.0
                
                total_ot = sum(max(Decimal("0.00"), r.total_hours - Decimal("8.00")) for r in attendances)
                avg_ot_hours = float(total_ot) / headcount

            insights_list.append(
                DepartmentInsights(
                    department_id=dept.id,
                    department_name=dept.name,
                    headcount=headcount,
                    total_monthly_payroll=total_payroll,
                    average_salary=avg_salary,
                    average_attendance_rate=float(avg_att_rate),
                    average_overtime_hours=float(avg_ot_hours),
                )
            )
            
        return insights_list

    async def get_ai_prediction_dataset(self) -> AIPredictionDataset:
        """Generate a structured dataset for machine learning models and anomaly detection."""
        emp_stmt = select(Employee).where(Employee.is_deleted == False)
        emp_res = await self.db_session.execute(emp_stmt)
        employees = emp_res.scalars().all()
        
        today = date.today()
        dataset_rows = []
        
        for emp in employees:
            tenure_days = (today - emp.hire_date).days
            
            # Attendance metrics
            att_stmt = select(Attendance).where(Attendance.employee_id == emp.id)
            att_res = await self.db_session.execute(att_stmt)
            attendances = att_res.scalars().all()
            
            total_att = len(attendances)
            att_rate = 100.0
            late_rate = 0.0
            total_ot = 0.0
            anomaly_flags = 0
            
            if total_att > 0:
                present_or_late = sum(
                    1 for r in attendances if r.attendance_status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE)
                )
                att_rate = (present_or_late / total_att) * 100.0
                
                late_count = sum(1 for r in attendances if r.attendance_status == AttendanceStatus.LATE)
                late_rate = (late_count / total_att) * 100.0
                
                total_ot = sum(max(Decimal("0.00"), r.total_hours - Decimal("8.00")) for r in attendances)
                
                # Rule-based Anomaly detection:
                # 1. Checked in during weekends
                # 2. Checked in at odd hours (between 11 PM and 4 AM)
                # 3. Total daily hours worked exceeds 14 hours (safety hazard)
                for att in attendances:
                    if att.check_in_time.weekday() >= 5:
                        anomaly_flags += 1
                    elif att.check_in_time.hour >= 23 or att.check_in_time.hour <= 4:
                        anomaly_flags += 1
                    if att.total_hours > Decimal("14.00"):
                        anomaly_flags += 1

            # Leave metrics
            leave_stmt = select(LeaveRequest).where(LeaveRequest.employee_id == emp.id)
            leave_res = await self.db_session.execute(leave_stmt)
            leaves = leave_res.scalars().all()
            
            leave_requests_count = len(leaves)
            leave_days_taken = sum(l.total_days for l in leaves if l.status == LeaveStatus.APPROVED)
            
            # Turnover risk classification:
            # 2 (High) if tenure is short and leave requests are high, or if late check-ins exceed 30%
            # 1 (Medium) if late check-ins exceed 15% or attendance rate is low (< 80%)
            # 0 (Low) otherwise
            turnover_risk = 0
            if (late_rate > 30.0) or (leave_requests_count > 5 and tenure_days < 180):
                turnover_risk = 2
            elif (late_rate > 15.0) or (att_rate < 80.0) or (anomaly_flags > 3):
                turnover_risk = 1

            dataset_rows.append(
                AIPredictionDatasetRow(
                    employee_id=emp.id,
                    tenure_days=tenure_days,
                    base_salary=emp.base_salary,
                    attendance_rate=float(att_rate),
                    late_rate=float(late_rate),
                    total_overtime_hours=float(total_ot),
                    leave_requests_count=leave_requests_count,
                    leave_days_taken=leave_days_taken,
                    anomaly_flags_count=anomaly_flags,
                    turnover_risk_label=turnover_risk,
                )
            )

        return AIPredictionDataset(
            generated_at=datetime.now(timezone.utc),
            data=dataset_rows,
        )

    async def get_turnover_risk_overview(self) -> TurnoverRiskOverview:
        """Calculate workforce attrition flight risks, driver breakdowns, and HR retention interventions."""
        emp_stmt = (
            select(Employee)
            .where(Employee.is_deleted == False)  # noqa: E712
            .options(selectinload(Employee.user), selectinload(Employee.department))
        )
        emp_res = await self.db_session.execute(emp_stmt)
        employees = list(emp_res.scalars().all())

        if not employees:
            return TurnoverRiskOverview(
                total_evaluated=0,
                low_risk_count=0,
                medium_risk_count=0,
                high_risk_count=0,
                critical_risk_count=0,
                average_workforce_risk_score=0.0,
                highest_risk_employees=[],
                department_risk_summary={},
            )

        evaluated_list: List[EmployeeTurnoverRiskDetail] = []
        dept_scores: Dict[str, List[float]] = {}

        today = date.today()

        for emp in employees:
            detail = await self._calculate_employee_flight_risk(emp, today)
            evaluated_list.append(detail)

            dept_name = emp.department.name if emp.department else "Unassigned"
            dept_scores.setdefault(dept_name, []).append(detail.risk_score)

        # Sort highest risk first
        evaluated_list.sort(key=lambda x: x.risk_score, reverse=True)

        low = sum(1 for e in evaluated_list if e.risk_level == "LOW")
        med = sum(1 for e in evaluated_list if e.risk_level == "MEDIUM")
        high = sum(1 for e in evaluated_list if e.risk_level == "HIGH")
        crit = sum(1 for e in evaluated_list if e.risk_level == "CRITICAL")

        avg_score = sum(e.risk_score for e in evaluated_list) / len(evaluated_list)

        dept_summary = {
            d: round(sum(scores) / len(scores), 1)
            for d, scores in dept_scores.items()
        }

        return TurnoverRiskOverview(
            total_evaluated=len(evaluated_list),
            low_risk_count=low,
            medium_risk_count=med,
            high_risk_count=high,
            critical_risk_count=crit,
            average_workforce_risk_score=round(avg_score, 1),
            highest_risk_employees=evaluated_list[:10],
            department_risk_summary=dept_summary,
        )

    async def get_employee_turnover_risk(self, employee_id: UUID) -> EmployeeTurnoverRiskDetail:
        """Deep dive flight risk analysis for a single employee."""
        emp_stmt = (
            select(Employee)
            .where(Employee.id == employee_id, Employee.is_deleted == False)  # noqa: E712
            .options(selectinload(Employee.user), selectinload(Employee.department))
        )
        emp_res = await self.db_session.execute(emp_stmt)
        emp = emp_res.scalar_one_or_none()
        if not emp:
            raise ValueError(f"Employee '{employee_id}' not found.")

        return await self._calculate_employee_flight_risk(emp, date.today())

    async def _calculate_employee_flight_risk(self, emp: Employee, today: date) -> EmployeeTurnoverRiskDetail:
        """Internal multi-dimensional flight risk scorer."""
        tenure_days = (today - emp.hire_date).days

        # Attendance metrics
        att_stmt = select(Attendance).where(Attendance.employee_id == emp.id)
        att_res = await self.db_session.execute(att_stmt)
        attendances = list(att_res.scalars().all())

        total_att = len(attendances)
        att_rate = 100.0
        late_rate = 0.0
        total_ot = 0.0

        if total_att > 0:
            present_or_late = sum(
                1 for r in attendances if r.attendance_status in (AttendanceStatus.PRESENT, AttendanceStatus.LATE)
            )
            att_rate = (present_or_late / total_att) * 100.0
            late_count = sum(1 for r in attendances if r.attendance_status == AttendanceStatus.LATE)
            late_rate = (late_count / total_att) * 100.0
            total_ot = sum(max(0.0, float(r.total_hours) - 8.0) for r in attendances)

        # Leave metrics
        leave_stmt = select(LeaveRequest).where(LeaveRequest.employee_id == emp.id)
        leave_res = await self.db_session.execute(leave_stmt)
        leaves = list(leave_res.scalars().all())
        leave_requests_count = len(leaves)

        # Compute Risk Score & Risk Drivers
        score = 15.0  # baseline natural turnover propensity
        drivers = []
        actions = []

        # 1. Overtime Burnout Factor (Weight: up to 35 pts)
        if total_ot >= 20.0:
            score += 35.0
            drivers.append(f"Severe Overtime Overload ({total_ot:.1f} hrs OT)")
            actions.append("Workload rebalancing & mandatory compensatory rest days")
        elif total_ot >= 10.0:
            score += 20.0
            drivers.append(f"Elevated Overtime ({total_ot:.1f} hrs OT)")
            actions.append("Review project resource allocations")

        # 2. Disengagement & Lateness Factor (Weight: up to 30 pts)
        if late_rate >= 35.0:
            score += 30.0
            drivers.append(f"Chronic Lateness Pattern ({late_rate:.0f}% late check-ins)")
            actions.append("1-on-1 check-in & flexible work hours consultation")
        elif late_rate >= 15.0:
            score += 15.0
            drivers.append(f"Frequent Late Arrivals ({late_rate:.0f}% late rate)")
            actions.append("Schedule informal pulse check with manager")

        # 3. Attendance Irregularity (Weight: up to 25 pts)
        if att_rate < 75.0:
            score += 25.0
            drivers.append(f"Significant Absenteeism ({att_rate:.0f}% attendance rate)")
            actions.append("Investigate potential health or workplace friction issues")
        elif att_rate < 85.0:
            score += 12.0
            drivers.append(f"Moderate Attendance Dip ({att_rate:.0f}%)")

        # 4. Tenure Flight Zone (Weight: up to 15 pts)
        if 90 <= tenure_days <= 240 and leave_requests_count >= 3:
            score += 15.0
            drivers.append(f"Mid-Probation/Early Tenure Flight Window ({tenure_days} days)")
            actions.append("Quarterly career progression & mentorship check-in")

        # Clamp score between 5.0 and 98.0
        score = max(5.0, min(98.0, round(score, 1)))

        if score >= 75.0:
            risk_level = "CRITICAL"
        elif score >= 55.0:
            risk_level = "HIGH"
        elif score >= 35.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        if not actions:
            actions.append("Maintain standard quarterly recognition and feedback cadence")

        return EmployeeTurnoverRiskDetail(
            employee_id=emp.id,
            employee_email=emp.user.email if emp.user else None,
            department_name=emp.department.name if emp.department else "Unassigned",
            risk_score=score,
            risk_level=risk_level,
            tenure_days=tenure_days,
            attendance_rate=round(att_rate, 1),
            late_rate=round(late_rate, 1),
            overtime_hours=round(total_ot, 1),
            leave_requests_count=leave_requests_count,
            primary_risk_drivers=drivers or ["No anomalous flight indicators detected"],
            recommended_interventions=actions,
        )

