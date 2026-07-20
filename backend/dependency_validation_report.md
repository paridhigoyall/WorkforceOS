# Dependency Validation Report

This report lists all broken imports, non-existent references, and schema/repository mismatches.

### ❌ Found 139 Dependency Issues

| File | Line | Type | Details |
| --- | --- | --- | --- |
| `backend\app\api\dependencies\auth.py` | 4 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\api\dependencies\auth.py` | 54 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: user_id = UUID(user_id_str)` |
| `backend\app\api\dependencies\auth.py` | 63 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: query = select(User).where(User.id == user_id, User.is_deleted == False)` |
| `backend\app\api\routes\attendance.py` | 12 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\api\routes\attendance.py` | 31 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_employee_for_user(db: AsyncSession, user_id: UUID):` |
| `backend\app\api\routes\attendance.py` | 87 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\attendance.py` | 128 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\attendance.py` | 162 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Optional[UUID] = Query(None, description="Filter by employee UUID"),` |
| `backend\app\api\routes\departments.py` | 2 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\api\routes\departments.py` | 72 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\departments.py` | 93 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\departments.py` | 118 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\employees.py` | 2 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\api\routes\employees.py` | 55 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: department_id: Optional[UUID] = Query(None, description="Filter by department UUID"),` |
| `backend\app\api\routes\employees.py` | 77 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\employees.py` | 109 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\employees.py` | 155 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\leave.py` | 14 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\api\routes\leave.py` | 40 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_employee_for_user(db: AsyncSession, user_id: UUID):` |
| `backend\app\api\routes\leave.py` | 103 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Optional[UUID] = Query(None, description="Filter by employee UUID"),` |
| `backend\app\api\routes\leave.py` | 139 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\leave.py` | 169 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\leave.py` | 187 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\leave.py` | 208 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: UUID,` |
| `backend\app\api\routes\leave.py` | 264 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: balance_id: UUID,` |
| `backend\app\api\routes\leave.py` | 286 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: UUID,` |
| `backend\app\models\attendance.py` | 6 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\models\attendance.py` | 11 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin` |
| `backend\app\models\attendance.py` | 24 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: class Attendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):` |
| `backend\app\models\attendance.py` | 28 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: Inherits UUIDPrimaryKeyMixin (id) and TimestampMixin (created_at, updated_at).` |
| `backend\app\models\attendance.py` | 32 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\audit_log.py` | 5 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\models\audit_log.py` | 11 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin` |
| `backend\app\models\audit_log.py` | 17 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):` |
| `backend\app\models\audit_log.py` | 28 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: user_id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\audit_log.py` | 33 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: comment="UUID of the user who triggered this audit event"` |
| `backend\app\models\audit_log.py` | 52 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: # Target entity UUID` |
| `backend\app\models\audit_log.py` | 53 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: target_id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\audit_log.py` | 57 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: comment="UUID of the specific entity affected by this action"` |
| `backend\app\models\base.py` | 8 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from sqlalchemy.dialects.postgresql import UUID as PGUUID` |
| `backend\app\models\base.py` | 44 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: ``is_deleted`` flags a record as removed without physical deletion.` |
| `backend\app\models\base.py` | 48 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: is_deleted: Mapped[bool] = Column(` |
| `backend\app\models\base.py` | 61 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: class UUIDPrimaryKeyMixin:` |
| `backend\app\models\base.py` | 62 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: """Mixin that adds a UUID primary key named ``id``.` |
| `backend\app\models\base.py` | 63 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: All models inheriting this mixin will have ``id`` as ``UUID`` type.` |
| `backend\app\models\base.py` | 66 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: Mapped[uuid.UUID] = Column(` |
| `backend\app\models\base.py` | 67 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: PGUUID(as_uuid=True),` |
| `backend\app\models\base.py` | 71 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: comment="Primary key UUID",` |
| `backend\app\models\department.py` | 3 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\models\department.py` | 17 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: Inherits TimestampMixin (created_at, updated_at) and SoftDeleteMixin (is_deleted, deleted_at)` |
| `backend\app\models\department.py` | 22 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\employee.py` | 5 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\models\employee.py` | 22 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: Inherits TimestampMixin (created_at, updated_at) and SoftDeleteMixin (is_deleted, deleted_at).` |
| `backend\app\models\employee.py` | 26 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\employee.py` | 36 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: user_id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\employee.py` | 46 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: department_id: Mapped[UUID | None] = mapped_column(` |
| `backend\app\models\leave.py` | 5 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: - Inherits from Base, UUIDPrimaryKeyMixin, and TimestampMixin` |
| `backend\app\models\leave.py` | 16 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\models\leave.py` | 21 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin` |
| `backend\app\models\leave.py` | 42 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: class LeaveRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):` |
| `backend\app\models\leave.py` | 46 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: Inherits UUIDPrimaryKeyMixin (id) and TimestampMixin (created_at, updated_at).` |
| `backend\app\models\leave.py` | 52 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\leave.py` | 99 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: approved_by: Mapped[Optional[UUID]] = mapped_column(` |
| `backend\app\models\leave.py` | 133 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: class LeaveBalance(Base, UUIDPrimaryKeyMixin, TimestampMixin):` |
| `backend\app\models\leave.py` | 140 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: Inherits UUIDPrimaryKeyMixin (id) and TimestampMixin (created_at, updated_at).` |
| `backend\app\models\leave.py` | 145 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Mapped[UUID] = mapped_column(` |
| `backend\app\models\user.py` | 10 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin` |
| `backend\app\models\user.py` | 21 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):` |
| `backend\app\models\user.py` | 24 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: * ``id`` – UUID primary key (provided by ``UUIDPrimaryKeyMixin``).` |
| `backend\app\models\__init__.py` | 3 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin` |
| `backend\app\models\__init__.py` | 15 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: "UUIDPrimaryKeyMixin",` |
| `backend\app\repositories\attendance_repository.py` | 14 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\repositories\attendance_repository.py` | 44 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_id(self, id: UUID) -> Optional[Attendance]:` |
| `backend\app\repositories\attendance_repository.py` | 54 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_employee_and_date(self, employee_id: UUID, attendance_date: date) -> Optional[Attendance]:` |
| `backend\app\repositories\attendance_repository.py` | 79 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Optional[UUID] = None,` |
| `backend\app\repositories\department_repository.py` | 3 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\repositories\department_repository.py` | 26 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[Department]:` |
| `backend\app\repositories\department_repository.py` | 27 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: """Fetch a department by its unique UUID."""` |
| `backend\app\repositories\department_repository.py` | 30 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: stmt = stmt.where(Department.is_deleted == False)` |
| `backend\app\repositories\department_repository.py` | 39 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: stmt = stmt.where(Department.is_deleted == False)` |
| `backend\app\repositories\department_repository.py` | 56 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: db_obj.is_deleted = True` |
| `backend\app\repositories\department_repository.py` | 77 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: query_stmt = query_stmt.where(Department.is_deleted == False)` |
| `backend\app\repositories\department_repository.py` | 78 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: count_stmt = count_stmt.where(Department.is_deleted == False)` |
| `backend\app\repositories\employee_repository.py` | 3 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\repositories\employee_repository.py` | 31 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[Employee]:` |
| `backend\app\repositories\employee_repository.py` | 33 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: Fetch an employee by their unique UUID.` |
| `backend\app\repositories\employee_repository.py` | 42 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: stmt = stmt.where(Employee.is_deleted == False)` |
| `backend\app\repositories\employee_repository.py` | 47 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_user_id(self, user_id: UUID, include_deleted: bool = False) -> Optional[Employee]:` |
| `backend\app\repositories\employee_repository.py` | 58 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: stmt = stmt.where(Employee.is_deleted == False)` |
| `backend\app\repositories\employee_repository.py` | 75 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: db_obj.is_deleted = True` |
| `backend\app\repositories\employee_repository.py` | 83 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: department_id: Optional[UUID] = None,` |
| `backend\app\repositories\employee_repository.py` | 101 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: query_stmt = query_stmt.where(Employee.is_deleted == False)` |
| `backend\app\repositories\employee_repository.py` | 102 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: count_stmt = count_stmt.where(Employee.is_deleted == False)` |
| `backend\app\repositories\leave_repository.py` | 15 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\repositories\leave_repository.py` | 33 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: UUID,` |
| `backend\app\repositories\leave_repository.py` | 56 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_id(self, id: UUID) -> Optional[LeaveRequest]:` |
| `backend\app\repositories\leave_repository.py` | 78 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: UUID,` |
| `backend\app\repositories\leave_repository.py` | 81 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: exclude_id: Optional[UUID] = None,` |
| `backend\app\repositories\leave_repository.py` | 109 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Optional[UUID] = None,` |
| `backend\app\repositories\leave_repository.py` | 154 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: UUID,` |
| `backend\app\repositories\leave_repository.py` | 183 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_by_id(self, id: UUID) -> Optional[LeaveBalance]:` |
| `backend\app\repositories\leave_repository.py` | 184 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: """Fetch a balance record by UUID."""` |
| `backend\app\repositories\leave_repository.py` | 206 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def increment_used(self, employee_id: UUID, leave_type: LeaveType, year: int, days: int) -> None:` |
| `backend\app\repositories\leave_repository.py` | 213 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def decrement_used(self, employee_id: UUID, leave_type: LeaveType, year: int, days: int) -> None:` |
| `backend\app\repositories\leave_repository.py` | 220 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def list_for_employee(self, employee_id: UUID, year: Optional[int] = None) -> List[LeaveBalance]:` |
| `backend\app\schemas\auth.py` | 95 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: is_deleted: bool` |
| `backend\app\schemas\department.py` | 59 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: is_deleted: bool` |
| `backend\app\schemas\employee.py` | 73 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: is_deleted: bool` |
| `backend\app\services\attendance_service.py` | 15 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\services\attendance_service.py` | 34 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def check_in(self, employee_id: UUID, check_in_time: Optional[datetime] = None) -> Attendance:` |
| `backend\app\services\attendance_service.py` | 47 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: Employee.is_deleted == False  # noqa: E712` |
| `backend\app\services\attendance_service.py` | 102 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def check_out(self, attendance_id: UUID, check_out_time: Optional[datetime] = None) -> Attendance:` |
| `backend\app\services\attendance_service.py` | 174 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_attendance(self, id: UUID) -> Attendance:` |
| `backend\app\services\attendance_service.py` | 183 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Optional[UUID] = None,` |
| `backend\app\services\auth_service.py` | 94 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: User.is_deleted == False,  # noqa: E712 — SQLAlchemy filter` |
| `backend\app\services\department_service.py` | 2 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\services\department_service.py` | 24 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: if existing.is_deleted:` |
| `backend\app\services\department_service.py` | 35 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_department(self, id: UUID) -> Department:` |
| `backend\app\services\department_service.py` | 50 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def update_department(self, id: UUID, schema: DepartmentUpdate) -> Department:` |
| `backend\app\services\department_service.py` | 67 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def delete_department(self, id: UUID) -> Department:` |
| `backend\app\services\employee_service.py` | 3 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\services\employee_service.py` | 22 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def onboard_employee(self, schema: EmployeeCreate, operator_id: UUID) -> Employee:` |
| `backend\app\services\employee_service.py` | 43 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: if existing_emp.is_deleted:` |
| `backend\app\services\employee_service.py` | 75 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_employee(self, id: UUID) -> Employee:` |
| `backend\app\services\employee_service.py` | 84 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: department_id: Optional[UUID] = None,` |
| `backend\app\services\employee_service.py` | 95 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def update_employee(self, id: UUID, schema: EmployeeUpdate, operator_id: UUID) -> Employee:` |
| `backend\app\services\employee_service.py` | 132 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def offboard_employee(self, id: UUID, operator_id: UUID) -> Employee:` |
| `backend\app\services\leave_service.py` | 17 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: from uuid import UUID` |
| `backend\app\services\leave_service.py` | 41 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def _require_employee(self, employee_id: UUID) -> Employee:` |
| `backend\app\services\leave_service.py` | 48 | **is_deleted Reference** | `References 'is_deleted' which is not in DB models: Employee.is_deleted == False,  # noqa: E712` |
| `backend\app\services\leave_service.py` | 64 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def apply(self, schema: LeaveRequestCreate, requesting_user_id: UUID) -> LeaveRequest:` |
| `backend\app\services\leave_service.py` | 131 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def approve(self, leave_id: UUID, approver_user_id: UUID) -> LeaveRequest:` |
| `backend\app\services\leave_service.py` | 195 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def reject(self, leave_id: UUID, approver_user_id: UUID) -> LeaveRequest:` |
| `backend\app\services\leave_service.py` | 252 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def cancel(self, leave_id: UUID, requesting_user_id: UUID) -> LeaveRequest:` |
| `backend\app\services\leave_service.py` | 313 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: async def get_leave(self, leave_id: UUID) -> LeaveRequest:` |
| `backend\app\services\leave_service.py` | 322 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: employee_id: Optional[UUID] = None,` |
| `backend\app\services\leave_service.py` | 340 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: self, schema: LeaveBalanceCreate, requesting_user_id: UUID` |
| `backend\app\services\leave_service.py` | 370 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: self, balance_id: UUID, schema: LeaveBalanceUpdate, requesting_user_id: UUID` |
| `backend\app\services\leave_service.py` | 400 | **UUID Reference** | `References UUID which is inconsistent with Integer PKs: self, employee_id: UUID, year: Optional[int] = None` |
