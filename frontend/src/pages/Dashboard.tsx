import React, { useEffect, useState } from 'react';
import { Users, Building2, Clock, Calendar, ArrowRight, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StatCard } from '../components/UI/StatCard';
import { employeesApi, departmentsApi, insightsApi, leaveApi } from '../api/endpoints';
import type { AttendanceInsights, LeaveInsights, LeaveRequest } from '../types';

export const Dashboard: React.FC = () => {
  const [employeeCount, setEmployeeCount] = useState<number>(0);
  const [departmentCount, setDepartmentCount] = useState<number>(0);
  const [attendanceInsights, setAttendanceInsights] = useState<AttendanceInsights | null>(null);
  const [leaveInsights, setLeaveInsights] = useState<LeaveInsights | null>(null);
  const [pendingLeaves, setPendingLeaves] = useState<LeaveRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [empRes, deptRes, attRes, leaveRes, pendingRes] = await Promise.allSettled([
          employeesApi.list(),
          departmentsApi.list(),
          insightsApi.getAttendance(),
          insightsApi.getLeave(),
          leaveApi.listRequests({ status: 'PENDING' })
        ]);

        if (empRes.status === 'fulfilled') setEmployeeCount(empRes.value.length);
        if (deptRes.status === 'fulfilled') setDepartmentCount(deptRes.value.length);
        if (attRes.status === 'fulfilled') setAttendanceInsights(attRes.value);
        if (leaveRes.status === 'fulfilled') setLeaveInsights(leaveRes.value);
        if (pendingRes.status === 'fulfilled') setPendingLeaves(pendingRes.value);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Header */}
      <div>
        <h1 className="page-title">Workspace Dashboard</h1>
        <p className="page-subtitle">Real-time overview of workforce operations, attendance, and leave management</p>
      </div>

      {/* KPI Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
        <StatCard
          title="Total Workforce"
          value={loading ? '...' : employeeCount}
          subtitle="Active employees"
          icon={Users}
          color="var(--primary)"
        />
        <StatCard
          title="Departments"
          value={loading ? '...' : departmentCount}
          subtitle="Operational units"
          icon={Building2}
          color="var(--accent-cyan)"
        />
        <StatCard
          title="Attendance Rate"
          value={loading || !attendanceInsights ? '...' : `${attendanceInsights.average_attendance_rate.toFixed(1)}%`}
          subtitle={`Late rate: ${attendanceInsights?.late_rate ? attendanceInsights.late_rate.toFixed(1) : 0}%`}
          icon={Clock}
          color="var(--accent-emerald)"
        />
        <StatCard
          title="Pending Leaves"
          value={loading || !leaveInsights ? '...' : leaveInsights.pending_requests}
          subtitle={`${leaveInsights?.approved_requests || 0} approved this cycle`}
          icon={Calendar}
          color="var(--accent-amber)"
        />
      </div>

      {/* AI Risk Alert Banner */}
      <div className="glass-panel" style={{
        padding: '24px',
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1))',
        border: '1px solid rgba(99, 102, 241, 0.3)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'var(--primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff'
          }}>
            <ShieldCheck size={24} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>AI Predictive Analytics Engine Active</h3>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Turnover risk indicators and attendance anomaly checks are continuously updating.
            </p>
          </div>
        </div>
        <Link to="/insights" className="btn btn-primary" style={{ fontSize: '0.8125rem' }}>
          <span>View Insights & Predictions</span>
          <ArrowRight size={16} />
        </Link>
      </div>

      {/* Two Column Section */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '28px' }}>
        {/* Attendance Summary Panel */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>Attendance Metrics</h3>
            <Link to="/attendance" style={{ color: 'var(--accent-cyan)', fontSize: '0.8125rem', textDecoration: 'none', fontWeight: 600 }}>
              View Logs
            </Link>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Average Daily Hours Worked</span>
              <span style={{ fontWeight: 700, color: '#fff' }}>
                {attendanceInsights?.average_daily_hours ? `${attendanceInsights.average_daily_hours.toFixed(1)} hrs` : 'N/A'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Total Overtime Hours</span>
              <span style={{ fontWeight: 700, color: 'var(--accent-emerald)' }}>
                {attendanceInsights?.total_overtime_hours ? `${attendanceInsights.total_overtime_hours.toFixed(1)} hrs` : '0 hrs'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Late Check-in Count</span>
              <span style={{ fontWeight: 700, color: 'var(--accent-amber)' }}>
                {attendanceInsights?.late_check_ins ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Pending Leave Requests Panel */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fff' }}>Pending Leave Approvals</h3>
            <Link to="/leave" style={{ color: 'var(--accent-cyan)', fontSize: '0.8125rem', textDecoration: 'none', fontWeight: 600 }}>
              Manage All
            </Link>
          </div>

          {pendingLeaves.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.875rem' }}>
              No pending leave requests at this time.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {pendingLeaves.slice(0, 3).map((req) => (
                <div key={req.id} style={{
                  padding: '12px 16px',
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: '10px',
                  border: '1px solid var(--glass-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <div>
                    <span style={{ fontWeight: 700, color: '#fff', fontSize: '0.875rem' }}>{req.leave_type} LEAVE</span>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {req.start_date} to {req.end_date}
                    </p>
                  </div>
                  <span className="badge badge-warning">Pending</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
