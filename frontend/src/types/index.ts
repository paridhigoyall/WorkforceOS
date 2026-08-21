export type UserRole = 'admin' | 'hr' | 'staff';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  name: string;
  description?: string;
  code: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
}

export interface Employee {
  id: string;
  user_id: string;
  department_id?: string;
  hire_date: string;
  phone?: string;
  base_salary: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  department?: Department;
  user?: User;
}

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  date: string;
  check_in?: string;
  check_out?: string;
  status: 'PRESENT' | 'ABSENT' | 'LATE' | 'HALF_DAY';
  hours_worked: number;
  overtime_hours: number;
  employee?: Employee;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  leave_type: 'ANNUAL' | 'SICK' | 'MATERNITY' | 'UNPAID' | 'CASUAL';
  start_date: string;
  end_date: string;
  reason?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  approved_by?: string;
  created_at: string;
  updated_at: string;
  employee?: Employee;
}

export interface LeaveBalance {
  id: string;
  employee_id: string;
  leave_type: string;
  allocated_days: number;
  used_days: number;
  remaining_days: number;
  year: number;
}

export interface AttendanceInsights {
  total_records: number;
  average_attendance_rate: number;
  late_check_ins: number;
  late_rate: number;
  total_overtime_hours: number;
  total_under_hours: number;
  average_daily_hours: number;
}

export interface LeaveInsights {
  total_requests: number;
  approved_requests: number;
  pending_requests: number;
  rejected_requests: number;
  cancelled_requests: number;
  total_days_taken: number;
  days_taken_by_type: Record<string, number>;
  utilization_rate: number;
}

export interface DepartmentInsights {
  department_id: string;
  department_name: string;
  headcount: number;
  total_monthly_payroll: number;
  average_salary: number;
  average_attendance_rate: number;
  average_overtime_hours: number;
}

export interface AIPredictionRow {
  employee_id: string;
  tenure_days: number;
  base_salary: number;
  attendance_rate: number;
  late_rate: number;
  total_overtime_hours: number;
  leave_requests_count: number;
  leave_days_taken: number;
  anomaly_flags_count: number;
  turnover_risk_label: 0 | 1 | 2; // 0: Low, 1: Medium, 2: High
}

export interface AIPredictionDataset {
  generated_at: string;
  data: AIPredictionRow[];
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  user_email?: string;
  action: string;
  target_type: string;
  target_id: string;
  details?: Record<string, any>;
  created_at: string;
}

export interface AuditLogListResponse {
  total: number;
  items: AuditLogEntry[];
  limit: number;
  offset: number;
}

export interface PayrollRecord {
  id: string;
  payroll_period_id: string;
  employee_id: string;
  employee_email?: string;
  department_name?: string;
  base_salary: number;
  overtime_hours: number;
  overtime_pay: number;
  unpaid_leave_days: number;
  unpaid_leave_deduction: number;
  tax_deduction: number;
  net_pay: number;
  status: 'PENDING' | 'PAID';
  created_at: string;
}

export interface PayrollPeriod {
  id: string;
  year: number;
  month: number;
  status: 'DRAFT' | 'PROCESSING' | 'APPROVED' | 'PAID';
  total_gross_pay: number;
  total_deductions: number;
  total_net_pay: number;
  employee_count: number;
  approved_at?: string;
  created_at: string;
  records?: PayrollRecord[];
}

export interface PayslipDetail {
  id: string;
  period_year: number;
  period_month: number;
  employee_id: string;
  employee_email?: string;
  department_name?: string;
  base_salary: number;
  overtime_hours: number;
  overtime_pay: number;
  unpaid_leave_days: number;
  unpaid_leave_deduction: number;
  gross_earnings: number;
  total_deductions: number;
  tax_deduction: number;
  net_pay: number;
  status: 'PENDING' | 'PAID';
  generated_at: string;
}

