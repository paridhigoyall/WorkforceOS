"""add_mfa_notifications_payroll

Revision ID: e8c1b3f99012
Revises: d0a539fe0864
Create Date: 2026-08-21 14:00:00.000000+00:00
"""
from __future__ import annotations

from typing import Sequence, Union
from alembic import context, op
import sqlalchemy as sa


revision: str = 'e8c1b3f99012'
down_revision: Union[str, Sequence[str], None] = 'd0a539fe0864'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add MFA columns to users table if not existing
    if context.is_offline_mode():
        user_cols = []
        tables = []
    else:
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        user_cols = [c['name'] for c in inspector.get_columns('users')]
        tables = inspector.get_table_names()
    
    if 'is_mfa_enabled' not in user_cols:
        op.add_column('users', sa.Column('is_mfa_enabled', sa.Boolean(), nullable=False, server_default='false'))
    if 'mfa_secret' not in user_cols:
        op.add_column('users', sa.Column('mfa_secret', sa.String(length=64), nullable=True))

    # 2. Create notifications table if not existing
    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.UUID(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('type', sa.Enum('info', 'success', 'warning', 'error', 'leave', 'attendance', 'payroll', name='notificationtype', native_enum=False, length=30), nullable=False),
            sa.Column('link', sa.String(length=500), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
        op.create_index(op.f('ix_notifications_is_read'), 'notifications', ['is_read'], unique=False)

    # 3. Create payroll tables if not existing
    if 'payroll_periods' not in tables:
        op.create_table(
            'payroll_periods',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('month', sa.Integer(), nullable=False),
            sa.Column('status', sa.Enum('DRAFT', 'APPROVED', 'PAID', name='payrollperiodstatus', native_enum=False, length=20), nullable=False),
            sa.Column('total_gross_pay', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
            sa.Column('total_deductions', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
            sa.Column('total_net_pay', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0.00'),
            sa.Column('employee_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_payroll_periods_year_month'), 'payroll_periods', ['year', 'month'], unique=False)

    if 'payroll_records' not in tables:
        op.create_table(
            'payroll_records',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('payroll_period_id', sa.UUID(), nullable=False),
            sa.Column('employee_id', sa.UUID(), nullable=False),
            sa.Column('base_salary', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('overtime_hours', sa.Numeric(precision=6, scale=2), nullable=False, server_default='0.00'),
            sa.Column('overtime_pay', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('unpaid_leave_days', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('unpaid_leave_deduction', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('tax_deduction', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('net_pay', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
            sa.Column('status', sa.Enum('PENDING', 'PAID', name='payrollrecordstatus', native_enum=False, length=20), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['payroll_period_id'], ['payroll_periods.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_payroll_records_payroll_period_id'), 'payroll_records', ['payroll_period_id'], unique=False)
        op.create_index(op.f('ix_payroll_records_employee_id'), 'payroll_records', ['employee_id'], unique=False)


def downgrade() -> None:
    op.drop_table('payroll_records')
    op.drop_table('payroll_periods')
    op.drop_table('notifications')
    op.drop_column('users', 'mfa_secret')
    op.drop_column('users', 'is_mfa_enabled')
