import { apiClient } from './client';
import type {
  User,
  Department,
  Employee,
  AttendanceRecord,
  LeaveRequest,
  LeaveBalance,
  AttendanceInsights,
  LeaveInsights,
  DepartmentInsights,
  AIPredictionDataset,
  AuditLogListResponse,
  PayrollPeriod,
  PayslipDetail
} from '../types';


export const authApi = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    const response = await apiClient.post<{ access_token: string; token_type: string }>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  },
  register: async (data: { email: string; password: string; role?: string }) => {
    const response = await apiClient.post<{ user: User; access_token: string }>('/auth/register', data);
    return response.data;
  },
  getMe: async () => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  }
};

export const departmentsApi = {
  list: async () => {
    const response = await apiClient.get<Department[]>('/departments');
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get<Department>(`/departments/${id}`);
    return response.data;
  },
  create: async (data: { name: string; code: string; description?: string }) => {
    const response = await apiClient.post<Department>('/departments', data);
    return response.data;
  },
  update: async (id: string, data: { name?: string; description?: string }) => {
    const response = await apiClient.patch<Department>(`/departments/${id}`, data);
    return response.data;
  },
  delete: async (id: string) => {
    const response = await apiClient.delete(`/departments/${id}`);
    return response.data;
  }
};

export const employeesApi = {
  list: async (departmentId?: string) => {
    const response = await apiClient.get<Employee[]>('/employees', {
      params: { department_id: departmentId }
    });
    return response.data;
  },
  get: async (id: string) => {
    const response = await apiClient.get<Employee>(`/employees/${id}`);
    return response.data;
  },
  onboard: async (data: { user_id: string; department_id?: string; hire_date: string; phone?: string; base_salary: number }) => {
    const response = await apiClient.post<Employee>('/employees/onboard', data);
    return response.data;
  },
  update: async (id: string, data: { department_id?: string; phone?: string; base_salary?: number }) => {
    const response = await apiClient.patch<Employee>(`/employees/${id}`, data);
    return response.data;
  },
  offboard: async (id: string) => {
    const response = await apiClient.post<Employee>(`/employees/${id}/offboard`);
    return response.data;
  }
};

export const attendanceApi = {
  checkIn: async () => {
    const response = await apiClient.post<AttendanceRecord>('/attendance/check-in');
    return response.data;
  },
  checkOut: async () => {
    const response = await apiClient.post<AttendanceRecord>('/attendance/check-out');
    return response.data;
  },
  list: async (params?: { employee_id?: string; start_date?: string; end_date?: string }) => {
    const response = await apiClient.get<AttendanceRecord[]>('/attendance', { params });
    return response.data;
  }
};

export const leaveApi = {
  apply: async (data: { leave_type: string; start_date: string; end_date: string; reason?: string }) => {
    const response = await apiClient.post<LeaveRequest>('/leave/requests', data);
    return response.data;
  },
  listRequests: async (params?: { employee_id?: string; status?: string }) => {
    const response = await apiClient.get<LeaveRequest[]>('/leave/requests', { params });
    return response.data;
  },
  approve: async (id: string) => {
    const response = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/approve`);
    return response.data;
  },
  reject: async (id: string) => {
    const response = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/reject`);
    return response.data;
  },
  cancel: async (id: string) => {
    const response = await apiClient.post<LeaveRequest>(`/leave/requests/${id}/cancel`);
    return response.data;
  },
  listBalances: async (employeeId?: string, year?: number) => {
    const response = await apiClient.get<LeaveBalance[]>('/leave/balances', {
      params: { employee_id: employeeId, year }
    });
    return response.data;
  }
};

export const insightsApi = {
  getAttendance: async () => {
    const response = await apiClient.get<AttendanceInsights>('/insights/attendance');
    return response.data;
  },
  getLeave: async () => {
    const response = await apiClient.get<LeaveInsights>('/insights/leave');
    return response.data;
  },
  getDepartments: async () => {
    const response = await apiClient.get<DepartmentInsights[]>('/insights/departments');
    return response.data;
  },
  getAIPredictions: async () => {
    const response = await apiClient.get<AIPredictionDataset>('/insights/ai-prediction-dataset');
    return response.data;
  }
};

export const auditLogsApi = {
  list: async (params?: { action?: string; target_type?: string; user_id?: string; limit?: number; offset?: number }) => {
    const response = await apiClient.get<AuditLogListResponse>('/audit-logs', { params });
    return response.data;
  }
};

export const payrollApi = {
  generate: async (data: { year: number; month: number }) => {
    const response = await apiClient.post<PayrollPeriod>('/payroll/generate', data);
    return response.data;
  },
  listPeriods: async (params?: { limit?: number; offset?: number }) => {
    const response = await apiClient.get<PayrollPeriod[]>('/payroll/periods', { params });
    return response.data;
  },
  getPeriod: async (id: string) => {
    const response = await apiClient.get<PayrollPeriod>(`/payroll/periods/${id}`);
    return response.data;
  },
  approvePeriod: async (id: string) => {
    const response = await apiClient.post<PayrollPeriod>(`/payroll/periods/${id}/approve`);
    return response.data;
  },
  getPayslip: async (recordId: string) => {
    const response = await apiClient.get<PayslipDetail>(`/payroll/records/${recordId}/payslip`);
    return response.data;
  }
};

