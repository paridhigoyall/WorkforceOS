import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts';
import { TrendingUp, ShieldAlert, Cpu, Award } from 'lucide-react';
import { insightsApi } from '../api/endpoints';
import { DepartmentInsights, LeaveInsights, AIPredictionDataset } from '../types';

export const Insights: React.FC = () => {
  const [deptInsights, setDeptInsights] = useState<DepartmentInsights[]>([]);
  const [leaveInsights, setLeaveInsights] = useState<LeaveInsights | null>(null);
  const [aiDataset, setAiDataset] = useState<AIPredictionDataset | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        const [dRes, lRes, aiRes] = await Promise.allSettled([
          insightsApi.getDepartments(),
          insightsApi.getLeave(),
          insightsApi.getAIPredictions()
        ]);

        if (dRes.status === 'fulfilled') setDeptInsights(dRes.value);
        if (lRes.status === 'fulfilled') setLeaveInsights(lRes.value);
        if (aiRes.status === 'fulfilled') setAiDataset(aiRes.value);
      } catch (err) {
        console.error('Failed to load insights:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, []);

  // Format data for Department Payroll Chart
  const payrollChartData = deptInsights.map((d) => ({
    name: d.department_name,
    payroll: Number(d.total_monthly_payroll),
    headcount: d.headcount
  }));

  // Format data for Leave Breakdown Chart
  const leavePieData = leaveInsights?.days_taken_by_type
    ? Object.entries(leaveInsights.days_taken_by_type).map(([name, value]) => ({ name, value }))
    : [];

  const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];

  const getRiskBadge = (label: number) => {
    switch (label) {
      case 0:
        return <span className="badge badge-success">Low Risk (0)</span>;
      case 1:
        return <span className="badge badge-warning">Medium Risk (1)</span>;
      case 2:
        return <span className="badge badge-danger">High Risk (2)</span>;
      default:
        return <span className="badge badge-info">{label}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Insights & Predictive Analytics</h1>
          <p className="page-subtitle">AI-driven turnover risk classification, department payroll analysis, and leave utilization</p>
        </div>
      </div>

      {/* Grid of Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '28px' }}>
        {/* Payroll by Department Chart */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>Monthly Payroll by Department</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Aggregated base salary expenses ($)</p>
          </div>

          <div style={{ width: '100%', height: '280px' }}>
            {loading || payrollChartData.length === 0 ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                No department payroll data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={payrollChartData}>
                  <XAxis dataKey="name" stroke="var(--text-dim)" fontSize={12} />
                  <YAxis stroke="var(--text-dim)" fontSize={12} />
                  <Tooltip
                    contentStyle={{ background: '#111827', borderColor: 'var(--glass-border)', borderRadius: '8px', color: '#fff' }}
                    formatter={(value: any) => [`$${Number(value).toLocaleString()}`, 'Payroll']}
                  />
                  <Bar dataKey="payroll" radius={[6, 6, 0, 0]}>
                    {payrollChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Leave Utilization Breakdown */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>Leave Days Distribution</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Breakdown of approved leave days by type</p>
          </div>

          <div style={{ width: '100%', height: '280px' }}>
            {loading || leavePieData.length === 0 ? (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                No leave distribution data available
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={leavePieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {leavePieData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#111827', borderColor: 'var(--glass-border)', borderRadius: '8px', color: '#fff' }} />
                  <Legend wrapperStyle={{ color: 'var(--text-muted)', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* AI Risk Prediction Table */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>AI Turnover Risk Prediction Dataset</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Features compiled for ML turnover prediction models</p>
          </div>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Tenure (Days)</th>
                <th>Attendance Rate</th>
                <th>Late Rate</th>
                <th>Overtime (Hrs)</th>
                <th>Leaves Taken</th>
                <th>Risk Label</th>
              </tr>
            </thead>
            <tbody>
              {loading || !aiDataset || aiDataset.data.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No AI dataset records available yet.
                  </td>
                </tr>
              ) : (
                aiDataset.data.map((row) => (
                  <tr key={row.employee_id}>
                    <td style={{ fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                      {row.employee_id.substring(0, 8)}...
                    </td>
                    <td>{row.tenure_days} days</td>
                    <td>{(row.attendance_rate * 100).toFixed(1)}%</td>
                    <td>{(row.late_rate * 100).toFixed(1)}%</td>
                    <td>{row.total_overtime_hours.toFixed(1)}</td>
                    <td>{row.leave_days_taken}</td>
                    <td>{getRiskBadge(row.turnover_risk_label)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
