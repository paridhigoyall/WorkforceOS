from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(DeclarativeBase):
    """Base class for all ORM models.
    It enables automatic typing support and allows unmapped attributes in mixins.
    """

    __abstract__ = True
    __allow_unmapped__ = True


class TimestampMixin:
    """Mixin adding ``created_at`` and ``updated_at`` timestamps.
    ``created_at`` defaults to ``func.now()`` and is not mutable.
    ``updated_at`` updates automatically on each flush.
    """

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp",
    )


class SoftDeleteMixin:
    """Mixin providing soft‑delete functionality.
    ``is_deleted`` flags a record as removed without physical deletion.
    ``deleted_at`` records when the soft delete occurred.
    """

    is_deleted: Mapped[bool] = Column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Logical deletion flag",
    )
    deleted_at: Mapped[datetime | None] = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of soft deletion",
    )


class UUIDPrimaryKeyMixin:
    """Mixin that adds a UUID primary key named ``id``.
    All models inheriting this mixin will have ``id`` as ``UUID`` type.
    """

    id: Mapped[uuid.UUID] = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Primary key UUID",
    )
