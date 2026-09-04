import React, { useEffect, useState, useCallback } from 'react';
import { DollarSign, Calendar, CheckCircle2, FileText, Plus, Printer } from 'lucide-react';
import { payrollApi } from '../api/endpoints';
import type { PayrollPeriod, PayrollRecord, PayslipDetail } from '../types';
import { Modal } from '../components/UI/Modal';
import { StatCard } from '../components/UI/StatCard';
import { useToast } from '../context/useToast';

export const Payroll: React.FC = () => {
  const toast = useToast();
  const [periods, setPeriods] = useState<PayrollPeriod[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<PayrollPeriod | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Generate Modal State
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState<boolean>(false);
  const [genYear, setGenYear] = useState<number>(new Date().getFullYear());
  const [genMonth, setGenMonth] = useState<number>(new Date().getMonth() + 1);
  const [genLoading, setGenLoading] = useState<boolean>(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Digital Payslip Modal State
  const [selectedPayslip, setSelectedPayslip] = useState<PayslipDetail | null>(null);
  const [, setPayslipLoading] = useState<boolean>(false);

  // My Payslips (self-service staff view)
  const [myPayslips, setMyPayslips] = useState<PayslipDetail[]>([]);
  const [myPayslipsLoading, setMyPayslipsLoading] = useState<boolean>(false);

  const fetchPayrollPeriods = useCallback(async () => {
    try {
      setLoading(true);
      const data = await payrollApi.listPeriods();
      setPeriods(data);
      if (data.length > 0) {
        setSelectedPeriod(prev => {
          if (!prev) {
            payrollApi.getPeriod(data[0].id).then(setSelectedPeriod).catch(console.error);
          }
          return prev;
        });
      }
    } catch (err) {
      console.error('Failed to fetch payroll periods:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMyPayslips = useCallback(async () => {
    try {
      setMyPayslipsLoading(true);
      const data = await payrollApi.getMyPayslips();
      setMyPayslips(data);
    } catch (err) {
      console.error('Failed to fetch personal payslips:', err);
    } finally {
      setMyPayslipsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPayrollPeriods();
    fetchMyPayslips();
  }, [fetchPayrollPeriods, fetchMyPayslips]);

  const handleSelectPeriod = async (periodId: string) => {
    try {
      setLoading(true);
      const data = await payrollApi.getPeriod(periodId);
      setSelectedPeriod(data);
    } catch (err) {
      console.error('Failed to load period details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenError(null);
    try {
      setGenLoading(true);
      const newPeriod = await payrollApi.generate({ year: genYear, month: genMonth });
      setIsGenerateModalOpen(false);
      setSelectedPeriod(newPeriod);
      fetchPayrollPeriods();
      toast.success(`Payroll period for ${genYear}-${String(genMonth).padStart(2, '0')} generated.`);
    } catch (err: any) {
      setGenError(err.response?.data?.detail || 'Failed to generate payroll batch.');
    } finally {
      setGenLoading(false);
    }
  };

  const handleApproveBatch = async () => {
    if (!selectedPeriod) return;
    try {
      setLoading(true);
      const approved = await payrollApi.approvePeriod(selectedPeriod.id);
      setSelectedPeriod(approved);
      fetchPayrollPeriods();
      toast.success('Payroll batch approved and marked as paid.');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Approval failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenPayslip = async (recordId: string) => {
    try {
      setPayslipLoading(true);
      const payslip = await payrollApi.getPayslip(recordId);
      setSelectedPayslip(payslip);
    } catch (err) {
      console.error('Failed to load digital payslip:', err);
      toast.error('Failed to load digital payslip.');
    } finally {
      setPayslipLoading(false);
    }
  };

  const handlePrintPayslip = () => {
    window.print();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Payroll & Compensation Management</h1>
          <p className="page-subtitle">Monthly salary calculations, overtime compensation, deductions, and digital payslips</p>
        </div>
        <button onClick={() => setIsGenerateModalOpen(true)} className="btn btn-primary">
          <Plus size={18} />
          <span>Generate Monthly Payroll</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
        <StatCard
          title="Total Net Payroll"
          value={selectedPeriod ? `$${selectedPeriod.total_net_pay.toLocaleString()}` : '$0'}
          subtitle={selectedPeriod ? `Batch: ${selectedPeriod.year}-${selectedPeriod.month.toString().padStart(2, '0')}` : 'No Period Selected'}
          icon={DollarSign}
          color="var(--accent-emerald)"
        />
        <StatCard
          title="Gross Payroll Cost"
          value={selectedPeriod ? `$${selectedPeriod.total_gross_pay.toLocaleString()}` : '$0'}
          subtitle="Before tax & deductions"
          icon={FileText}
          color="var(--primary)"
        />
        <StatCard
          title="Total Deductions"
          value={selectedPeriod ? `$${selectedPeriod.total_deductions.toLocaleString()}` : '$0'}
          subtitle="Tax & unpaid leave"
          icon={Calendar}
          color="var(--accent-rose)"
        />
        <StatCard
          title="Processed Employees"
          value={selectedPeriod ? selectedPeriod.employee_count : 0}
          subtitle={`Status: ${selectedPeriod?.status || 'N/A'}`}
          icon={CheckCircle2}
          color="var(--accent-cyan)"
        />
      </div>

      {/* Period Selection & Approval Bar */}
      <div style={{ display: 'flex', gap: '16px', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>Select Payroll Batch:</span>
          <select
            value={selectedPeriod?.id || ''}
            onChange={(e) => handleSelectPeriod(e.target.value)}
            className="input-field"
            style={{ width: '220px' }}
          >
            {periods.map((p) => (
              <option key={p.id} value={p.id}>
                {p.year} - Month {p.month.toString().padStart(2, '0')} ({p.status})
              </option>
            ))}
          </select>
        </div>

        {selectedPeriod && selectedPeriod.status === 'DRAFT' && (
          <button onClick={handleApproveBatch} className="btn btn-primary" style={{ background: 'var(--accent-emerald)' }}>
            <CheckCircle2 size={16} />
            <span>Approve Batch & Mark Paid</span>
          </button>
        )}
      </div>

      {/* Employee Payslips Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>
            Employee Payslips ({selectedPeriod ? `${selectedPeriod.year}-${selectedPeriod.month.toString().padStart(2, '0')}` : 'None'})
          </h3>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee Email</th>
                <th>Department</th>
                <th>Base Salary</th>
                <th>Overtime (Hrs/Pay)</th>
                <th>Unpaid Deductions</th>
                <th>Tax (10%)</th>
                <th>Net Pay</th>
                <th>Status</th>
                <th>Payslip</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    Loading payroll records...
                  </td>
                </tr>
              ) : !selectedPeriod || !selectedPeriod.records || selectedPeriod.records.length === 0 ? (
                <tr>
                  <td colSpan={9} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No payroll records available. Generate a monthly batch above.
                  </td>
                </tr>
              ) : (
                selectedPeriod.records.map((rec: PayrollRecord) => (
                  <tr key={rec.id}>
                    <td style={{ fontWeight: 600, color: '#fff' }}>
                      {rec.employee_email || rec.employee_id.substring(0, 8)}
                    </td>
                    <td style={{ color: 'var(--accent-cyan)' }}>{rec.department_name || 'Unassigned'}</td>
                    <td>${rec.base_salary.toLocaleString()}</td>
                    <td>
                      <span style={{ color: rec.overtime_hours > 0 ? 'var(--accent-emerald)' : 'inherit', fontWeight: rec.overtime_hours > 0 ? 700 : 400 }}>
                        {rec.overtime_hours} hrs (+${rec.overtime_pay.toLocaleString()})
                      </span>
                    </td>
                    <td style={{ color: rec.unpaid_leave_days > 0 ? 'var(--accent-rose)' : 'inherit' }}>
                      {rec.unpaid_leave_days} days (-${rec.unpaid_leave_deduction.toLocaleString()})
                    </td>
                    <td style={{ color: 'var(--text-muted)' }}>-${rec.tax_deduction.toLocaleString()}</td>
                    <td style={{ fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '0.9375rem' }}>
                      ${rec.net_pay.toLocaleString()}
                    </td>
                    <td>
                      <span className={`badge ${rec.status === 'PAID' ? 'badge-success' : 'badge-warning'}`}>
                        {rec.status}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleOpenPayslip(rec.id)}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem', color: 'var(--accent-cyan)' }}
                      >
                        <FileText size={14} />
                        <span>View Payslip</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* My Payslip History — self-service view for all employees */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--glass-border)' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>
            My Payslip History
          </h3>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Your personal payslips across all processed payroll periods.
          </p>
        </div>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Period</th>
                <th>Base Salary</th>
                <th>Overtime Pay</th>
                <th>Tax Deduction</th>
                <th>Net Pay</th>
                <th>Status</th>
                <th>Payslip</th>
              </tr>
            </thead>
            <tbody>
              {myPayslipsLoading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    Loading your payslips...
                  </td>
                </tr>
              ) : myPayslips.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No payslips available yet. Payslips appear here once payroll is approved.
                  </td>
                </tr>
              ) : (
                myPayslips.map((slip) => (
                  <tr key={slip.id}>
                    <td style={{ fontWeight: 600, color: '#fff' }}>
                      {slip.period_year}-{String(slip.period_month).padStart(2, '0')}
                    </td>
                    <td>${slip.base_salary.toLocaleString()}</td>
                    <td style={{ color: slip.overtime_pay > 0 ? 'var(--accent-emerald)' : 'inherit' }}>
                      +${slip.overtime_pay.toLocaleString()}
                    </td>
                    <td style={{ color: 'var(--accent-rose)' }}>-${slip.tax_deduction.toLocaleString()}</td>
                    <td style={{ fontWeight: 800, color: 'var(--accent-emerald)', fontSize: '0.9375rem' }}>
                      ${slip.net_pay.toLocaleString()}
                    </td>
                    <td>
                      <span className={`badge ${slip.status === 'PAID' ? 'badge-success' : 'badge-warning'}`}>
                        {slip.status}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => setSelectedPayslip(slip)}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem', color: 'var(--accent-cyan)' }}
                      >
                        <FileText size={14} />
                        <span>View</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generate Payroll Modal */}
      <Modal isOpen={isGenerateModalOpen} onClose={() => setIsGenerateModalOpen(false)} title="Generate Monthly Payroll Batch">
        {genError && (
          <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(244,63,94,0.15)', color: 'var(--accent-rose)', marginBottom: '16px', fontSize: '0.8125rem' }}>
            {genError}
          </div>
        )}
        <form onSubmit={handleGenerateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label className="input-label">Select Year</label>
            <input
              type="number"
              required
              min={2020}
              max={2100}
              value={genYear}
              onChange={(e) => setGenYear(parseInt(e.target.value))}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Select Month (1 - 12)</label>
            <select
              value={genMonth}
              onChange={(e) => setGenMonth(parseInt(e.target.value))}
              className="input-field"
            >
              {[1,2,3,4,5,6,7,8,9,10,11,12].map((m) => (
                <option key={m} value={m}>
                  Month {m.toString().padStart(2, '0')} ({new Date(2026, m - 1, 1).toLocaleString('default', { month: 'long' })})
                </option>
              ))}
            </select>
          </div>

          <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            Generating payroll will automatically calculate overtime pay from daily clock-ins and deductions for unpaid leave taken during this month.
          </p>

          <button type="submit" disabled={genLoading} className="btn btn-primary" style={{ marginTop: '8px' }}>
            <span>{genLoading ? 'Calculating...' : 'Run Payroll Calculations'}</span>
          </button>
        </form>
      </Modal>

      {/* Digital Printable Payslip Modal */}
      <Modal isOpen={!!selectedPayslip} onClose={() => setSelectedPayslip(null)} title="Official Digital Payslip">
        {selectedPayslip && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '10px' }}>
            {/* Enterprise Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid var(--primary)', paddingBottom: '16px' }}>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>WorkforceOS Enterprise</h2>
                <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Confidential Earnings Statement</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                  {selectedPayslip.period_year}-{selectedPayslip.period_month.toString().padStart(2, '0')}
                </span>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                  Status: {selectedPayslip.status}
                </p>
              </div>
            </div>

            {/* Employee Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.875rem', background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Employee Email: </span>
                <span style={{ fontWeight: 700, color: '#fff' }}>{selectedPayslip.employee_email}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Department: </span>
                <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{selectedPayslip.department_name || 'N/A'}</span>
              </div>
            </div>

            {/* Breakdown Table */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <span>Base Salary</span>
                <span style={{ fontWeight: 700, color: '#fff' }}>${selectedPayslip.base_salary.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <span>Overtime Compensation ({selectedPayslip.overtime_hours} hrs)</span>
                <span style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>+${selectedPayslip.overtime_pay.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--accent-rose)' }}>
                <span>Unpaid Leave Deductions ({selectedPayslip.unpaid_leave_days} days)</span>
                <span>-${selectedPayslip.unpaid_leave_deduction.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'var(--text-muted)' }}>
                <span>Income Tax (10%)</span>
                <span>-${selectedPayslip.tax_deduction.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', marginTop: '8px', borderTop: '2px solid var(--accent-emerald)', fontSize: '1.125rem', fontWeight: 800 }}>
                <span style={{ color: '#fff' }}>NET TAKE HOME PAY</span>
                <span style={{ color: 'var(--accent-emerald)' }}>${selectedPayslip.net_pay.toLocaleString()}</span>
              </div>
            </div>

            <button onClick={handlePrintPayslip} className="btn btn-secondary" style={{ marginTop: '12px', justifyContent: 'center' }}>
              <Printer size={16} />
              <span>Print Official Payslip</span>
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
};
