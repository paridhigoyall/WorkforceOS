import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend
} from 'recharts';
import { Cpu, ShieldCheck, Flame, UserCheck, Activity, Brain, RefreshCw } from 'lucide-react';
import { insightsApi } from '../api/endpoints';
import type { DepartmentInsights, LeaveInsights, AIPredictionDataset, TurnoverRiskOverview, EmployeeTurnoverRiskDetail, AIPredictionRow } from '../types';

export const Insights: React.FC = () => {
  const [deptInsights, setDeptInsights] = useState<DepartmentInsights[]>([]);
  const [leaveInsights, setLeaveInsights] = useState<LeaveInsights | null>(null);
  const [aiDataset, setAiDataset] = useState<AIPredictionDataset | null>(null);
  const [turnoverOverview, setTurnoverOverview] = useState<TurnoverRiskOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      const [dRes, lRes, aiRes, toRes] = await Promise.allSettled([
        insightsApi.getDepartments(),
        insightsApi.getLeave(),
        insightsApi.getAIPredictions(),
        insightsApi.getTurnoverRiskOverview(),
      ]);

      if (dRes.status === 'fulfilled') setDeptInsights(dRes.value);
      if (lRes.status === 'fulfilled') setLeaveInsights(lRes.value);
      if (aiRes.status === 'fulfilled') setAiDataset(aiRes.value);
      if (toRes.status === 'fulfilled') setTurnoverOverview(toRes.value);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  // Format data for Department Payroll Chart
  const payrollChartData = deptInsights.map((d: DepartmentInsights) => ({
    name: d.department_name,
    payroll: Number(d.total_monthly_payroll),
    headcount: d.headcount
  }));


  // Format data for Leave Breakdown Chart
  const leavePieData = leaveInsights?.days_taken_by_type
    ? Object.entries(leaveInsights.days_taken_by_type).map(([name, value]) => ({ name, value }))
    : [];

  const COLORS = ['#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#f43f5e'];

  const getRiskLevelBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return <span className="badge badge-danger" style={{ background: 'rgba(244,63,94,0.15)', border: '1px solid var(--accent-rose)' }}>🚨 CRITICAL</span>;
      case 'HIGH':
        return <span className="badge badge-danger">High Risk</span>;
      case 'MEDIUM':
        return <span className="badge badge-warning">Medium Risk</span>;
      case 'LOW':
      default:
        return <span className="badge badge-success">Low Risk</span>;
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score >= 75) return 'var(--accent-rose)';
    if (score >= 50) return 'var(--accent-amber)';
    if (score >= 25) return 'var(--accent-cyan)';
    return 'var(--accent-emerald)';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
            <h1 className="page-title" style={{ margin: 0 }}>AI Workforce Intelligence & Retention</h1>
            <span style={{
              padding: '4px 10px',
              borderRadius: '99px',
              background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.2))',
              border: '1px solid rgba(168,85,247,0.4)',
              color: 'var(--accent-purple)',
              fontSize: '0.75rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
            }}>
              <Brain size={13} /> ML Predictive Engine
            </span>
          </div>
          <p className="page-subtitle">Turnover flight risk matrix, automated retention recommendations, and workforce cost analytics</p>
        </div>

        <button
          onClick={fetchInsights}
          className="btn btn-secondary"
          style={{ gap: '8px' }}
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Analysis</span>
        </button>
      </div>

      {/* Top AI Flight Risk KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
        {/* Workforce Avg Risk */}
        <div className="glass-panel" style={{ padding: '20px', position: 'relative', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Avg Turnover Risk</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99,102,241,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Activity size={16} color="var(--primary)" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: getRiskScoreColor(turnoverOverview?.average_workforce_risk_score || 0), marginTop: '10px' }}>
            {turnoverOverview?.average_workforce_risk_score ?? 0}%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Across {turnoverOverview?.total_evaluated ?? 0} active employees
          </div>
        </div>

        {/* High / Critical Risk */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Elevated Flight Risk</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(244,63,94,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Flame size={16} color="var(--accent-rose)" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-rose)', marginTop: '10px' }}>
            {(turnoverOverview?.high_risk_count ?? 0) + (turnoverOverview?.critical_risk_count ?? 0)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            {turnoverOverview?.critical_risk_count ?? 0} critical, {turnoverOverview?.high_risk_count ?? 0} high
          </div>
        </div>

        {/* Stable / Low Risk */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Stable Retention</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(16,185,129,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={16} color="var(--accent-emerald)" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '10px' }}>
            {turnoverOverview?.low_risk_count ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Optimal tenure & attendance health
          </div>
        </div>

        {/* Dept Hotspot */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total Evaluated</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(6,182,212,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <UserCheck size={16} color="var(--accent-cyan)" />
            </div>
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', marginTop: '10px' }}>
            {turnoverOverview?.total_evaluated ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Real-time biometric & leave telemetry
          </div>
        </div>
      </div>

      {/* AI Turnover Flight Risk & Predictive Retention Matrix */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Brain size={20} color="#fff" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff', margin: 0 }}>
                AI Turnover Flight Risk & Retention Strategy Matrix
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: 0 }}>
                Identifies flight risk drivers and auto-generates personalized retention interventions
              </p>
            </div>
          </div>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Department</th>
                <th>Flight Risk Score</th>
                <th>Risk Level</th>
                <th>Primary Risk Drivers</th>
                <th>Recommended Interventions</th>
              </tr>
            </thead>
            <tbody>
              {loading || !turnoverOverview || turnoverOverview.highest_risk_employees.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                    No turnover risk evaluations found. Onboard employees and log attendance to generate predictions.
                  </td>
                </tr>
              ) : (
                turnoverOverview.highest_risk_employees.map((emp: EmployeeTurnoverRiskDetail) => (
                  <tr key={emp.employee_id}>
                    <td>
                      <div style={{ fontWeight: 700, color: '#fff' }}>
                        {emp.employee_email || `EMP-${emp.employee_id.substring(0, 6)}`}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                        Tenure: {emp.tenure_days} days | Overtime: {emp.overtime_hours.toFixed(1)}h
                      </div>
                    </td>
                    <td>
                      <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                        {emp.department_name || 'Unassigned'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          flex: 1,
                          height: '6px',
                          borderRadius: '99px',
                          background: 'rgba(255,255,255,0.08)',
                          overflow: 'hidden',
                          minWidth: '60px',
                        }}>
                          <div style={{
                            width: `${emp.risk_score}%`,
                            height: '100%',
                            background: getRiskScoreColor(emp.risk_score),
                            borderRadius: '99px',
                          }} />
                        </div>
                        <span style={{ fontWeight: 800, color: getRiskScoreColor(emp.risk_score), fontSize: '0.875rem' }}>
                          {emp.risk_score}%
                        </span>
                      </div>
                    </td>
                    <td>{getRiskLevelBadge(emp.risk_level)}</td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {emp.primary_risk_drivers.map((driver: string, i: number) => (
                          <span
                            key={i}
                            style={{
                              padding: '2px 8px',
                              borderRadius: '6px',
                              background: 'rgba(244,63,94,0.08)',
                              border: '1px solid rgba(244,63,94,0.2)',
                              color: '#fb7185',
                              fontSize: '0.71875rem',
                              fontWeight: 600,
                            }}
                          >
                            {driver}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {emp.recommended_interventions.map((action: string, i: number) => (
                          <span
                            key={i}
                            style={{
                              padding: '2px 8px',
                              borderRadius: '6px',
                              background: 'rgba(99,102,241,0.08)',
                              border: '1px solid rgba(99,102,241,0.2)',
                              color: 'var(--primary-light)',
                              fontSize: '0.71875rem',
                              fontWeight: 600,
                            }}
                          >
                            ✓ {action}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Grid of Standard Charts */}
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
                    {payrollChartData.map((_: any, index: number) => (
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
                    {leavePieData.map((_: any, index: number) => (
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

      {/* AI Risk Prediction Training Dataset */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Cpu size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff', margin: 0 }}>
              AI Model Training Dataset
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: 0 }}>
              Underlying multi-dimensional vector features computed for ML regression & classification
            </p>
          </div>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Tenure</th>
                <th>Attendance Rate</th>
                <th>Late Rate</th>
                <th>Overtime (Hrs)</th>
                <th>Leaves Taken</th>
                <th>Risk Tier Class</th>
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
                aiDataset.data.map((row: AIPredictionRow) => (
                  <tr key={row.employee_id}>
                    <td style={{ fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                      {row.employee_id.substring(0, 8)}...
                    </td>
                    <td>{row.tenure_days} days</td>
                    <td>{(row.attendance_rate * 100).toFixed(1)}%</td>
                    <td>{(row.late_rate * 100).toFixed(1)}%</td>
                    <td>{row.total_overtime_hours.toFixed(1)}</td>
                    <td>{row.leave_days_taken}</td>
                    <td>
                      {row.turnover_risk_label === 2 ? (
                        <span className="badge badge-danger">Class 2 (High)</span>
                      ) : row.turnover_risk_label === 1 ? (
                        <span className="badge badge-warning">Class 1 (Med)</span>
                      ) : (
                        <span className="badge badge-success">Class 0 (Low)</span>
                      )}
                    </td>
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

