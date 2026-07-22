import React, { useEffect, useState } from 'react';
import { UserPlus, Search, UserCheck, UserX, Phone, DollarSign, Calendar } from 'lucide-react';
import { employeesApi, departmentsApi } from '../api/endpoints';
import { Employee, Department } from '../types';
import { Modal } from '../components/UI/Modal';

export const Employees: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [selectedDept, setSelectedDept] = useState<string>('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [userId, setUserId] = useState<string>('');
  const [deptId, setDeptId] = useState<string>('');
  const [hireDate, setHireDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [phone, setPhone] = useState<string>('');
  const [baseSalary, setBaseSalary] = useState<number>(5000);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchEmployees = async () => {
    try {
      setLoading(true);
      const [empData, deptData] = await Promise.all([
        employeesApi.list(selectedDept || undefined),
        departmentsApi.list()
      ]);
      setEmployees(empData);
      setDepartments(deptData);
    } catch (err) {
      console.error('Failed to load employees:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, [selectedDept]);

  const handleOnboard = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setSubmitting(true);
    try {
      await employeesApi.onboard({
        user_id: userId,
        department_id: deptId || undefined,
        hire_date: hireDate,
        phone: phone || undefined,
        base_salary: Number(baseSalary)
      });
      setIsModalOpen(false);
      fetchEmployees();
    } catch (err: any) {
      setModalError(err.response?.data?.detail || 'Failed to onboard employee.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOffboard = async (id: string) => {
    if (!window.confirm('Are you sure you want to offboard this employee?')) return;
    try {
      await employeesApi.offboard(id);
      fetchEmployees();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to offboard employee.');
    }
  };

  const filteredEmployees = employees.filter((emp) => {
    const term = search.toLowerCase();
    const phoneMatch = emp.phone?.toLowerCase().includes(term);
    const idMatch = emp.id.toLowerCase().includes(term);
    return phoneMatch || idMatch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Workforce Directory</h1>
          <p className="page-subtitle">Manage employee profiles, onboarding, department assignments, and salary details</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          <UserPlus size={18} />
          <span>Onboard Employee</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, minWidth: '260px' }}>
          <input
            type="text"
            placeholder="Search by ID or Phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field"
            style={{ paddingLeft: '40px' }}
          />
          <Search size={18} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
        </div>

        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="input-field"
          style={{ width: '220px' }}
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>

      {/* Data Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Department</th>
                <th>Phone</th>
                <th>Hire Date</th>
                <th>Base Salary ($/mo)</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    Loading employee records...
                  </td>
                </tr>
              ) : filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No employees found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredEmployees.map((emp) => (
                  <tr key={emp.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                      {emp.id.substring(0, 8)}...
                    </td>
                    <td>
                      {emp.department ? (
                        <span className="badge badge-info">{emp.department.name}</span>
                      ) : (
                        <span style={{ color: 'var(--text-dim)' }}>Unassigned</span>
                      )}
                    </td>
                    <td>{emp.phone || 'N/A'}</td>
                    <td>{emp.hire_date}</td>
                    <td style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                      ${Number(emp.base_salary).toLocaleString()}
                    </td>
                    <td>
                      {emp.is_deleted ? (
                        <span className="badge badge-danger">Offboarded</span>
                      ) : (
                        <span className="badge badge-success">Active</span>
                      )}
                    </td>
                    <td>
                      {!emp.is_deleted && (
                        <button
                          onClick={() => handleOffboard(emp.id)}
                          className="btn btn-secondary"
                          style={{ padding: '6px 12px', fontSize: '0.75rem', color: 'var(--accent-rose)' }}
                        >
                          <UserX size={14} />
                          <span>Offboard</span>
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Onboard Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Onboard New Employee">
        {modalError && (
          <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(244,63,94,0.15)', color: 'var(--accent-rose)', marginBottom: '16px', fontSize: '0.8125rem' }}>
            {modalError}
          </div>
        )}
        <form onSubmit={handleOnboard} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label className="input-label">User Account UUID</label>
            <input
              type="text"
              required
              placeholder="e.g. 123e4567-e89b-12d3-a456-426614174000"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Department</label>
            <select
              value={deptId}
              onChange={(e) => setDeptId(e.target.value)}
              className="input-field"
            >
              <option value="">Select Department...</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.code})</option>
              ))}
            </select>
          </div>

          <div>
            <label className="input-label">Hire Date</label>
            <input
              type="date"
              required
              value={hireDate}
              onChange={(e) => setHireDate(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Phone (E.164 format)</label>
            <input
              type="text"
              placeholder="+1234567890"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Monthly Base Salary ($)</label>
            <input
              type="number"
              min="0"
              step="500"
              value={baseSalary}
              onChange={(e) => setBaseSalary(Number(e.target.value))}
              className="input-field"
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '12px' }}>
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn btn-primary">
              {submitting ? 'Processing...' : 'Complete Onboarding'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
