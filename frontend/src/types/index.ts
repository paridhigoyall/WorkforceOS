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
