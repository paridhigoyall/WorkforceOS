import uuid
from typing import TYPE_CHECKING, List
from uuid import UUID
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy model representing a Department.
    
    Inherits TimestampMixin (created_at, updated_at) and SoftDeleteMixin (is_deleted, deleted_at)
    from the base models module.
    """
    __tablename__ = "departments"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
        comment="Unique identifier for the department"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique name of the department"
    )

    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="Short uppercase department code, e.g. ENG, HR, FIN"
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Brief description of the department's purpose"
    )

    # Relationship with Employee
    # cascade="all, delete-orphan" handles cascading deletion of employees when department is deleted
    # passive_deletes=True allows database-level ON DELETE CASCADE configuration (highly recommended for performance)
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Department name={self.name!r} id={self.id}>"
