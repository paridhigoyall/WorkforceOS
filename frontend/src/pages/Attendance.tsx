import React, { useEffect, useState } from 'react';
import { attendanceApi } from '../api/endpoints';
import type { AttendanceRecord } from '../types';

export const Attendance: React.FC = () => {
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const fetchAttendance = async () => {
    try {
      setLoading(true);
      const data = await attendanceApi.list({
        start_date: startDate || undefined,
        end_date: endDate || undefined
      });
      setRecords(data);
    } catch (err) {
      console.error('Failed to fetch attendance logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
  }, [startDate, endDate]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PRESENT':
        return <span className="badge badge-success">Present</span>;
      case 'LATE':
        return <span className="badge badge-warning">Late</span>;
      case 'HALF_DAY':
        return <span className="badge badge-info">Half Day</span>;
      case 'ABSENT':
        return <span className="badge badge-danger">Absent</span>;
      default:
        return <span className="badge badge-info">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Attendance Logs</h1>
          <p className="page-subtitle">Daily clock-in/clock-out records, late check-in tracking, and overtime hours</p>
        </div>
      </div>

      {/* Date Filter Bar */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Start Date:</span>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="input-field"
            style={{ width: '180px' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>End Date:</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="input-field"
            style={{ width: '180px' }}
          />
        </div>

        {(startDate || endDate) && (
          <button
            onClick={() => { setStartDate(''); setEndDate(''); }}
            className="btn btn-secondary"
            style={{ padding: '8px 14px', fontSize: '0.8125rem' }}
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Attendance Log Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Employee ID</th>
                <th>Clock In</th>
                <th>Clock Out</th>
                <th>Hours Worked</th>
                <th>Overtime</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    Loading attendance logs...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No attendance records found for selected period.
                  </td>
                </tr>
              ) : (
                records.map((rec) => (
                  <tr key={rec.id}>
                    <td style={{ fontWeight: 600, color: '#fff' }}>{rec.date}</td>
                    <td style={{ fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                      {rec.employee_id.substring(0, 8)}...
                    </td>
                    <td>{rec.check_in ? new Date(rec.check_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}</td>
                    <td>{rec.check_out ? new Date(rec.check_out).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--:--'}</td>
                    <td style={{ fontWeight: 600 }}>
                      {rec.hours_worked ? `${rec.hours_worked.toFixed(1)} hrs` : '0 hrs'}
                    </td>
                    <td style={{ color: rec.overtime_hours > 0 ? 'var(--accent-emerald)' : 'var(--text-dim)', fontWeight: rec.overtime_hours > 0 ? 700 : 400 }}>
                      {rec.overtime_hours ? `+${rec.overtime_hours.toFixed(1)} hrs` : '0 hrs'}
                    </td>
                    <td>{getStatusBadge(rec.status)}</td>
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
