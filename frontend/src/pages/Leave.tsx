import React, { useEffect, useState, useCallback } from 'react';
import { Plus, CheckCircle2, XCircle } from 'lucide-react';
import { leaveApi } from '../api/endpoints';
import type { LeaveRequest, LeaveBalance } from '../types';
import { Modal } from '../components/UI/Modal';

export const Leave: React.FC = () => {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [leaveType, setLeaveType] = useState<string>('Casual');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchLeaveData = useCallback(async () => {
    try {
      setLoading(true);
      const [reqData, balData] = await Promise.all([
        leaveApi.listRequests({ status: statusFilter || undefined }),
        leaveApi.listBalances()
      ]);
      setRequests(reqData);
      setBalances(balData);
    } catch (err) {
      console.error('Failed to load leave data:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchLeaveData();
  }, [fetchLeaveData]);

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setSubmitting(true);
    try {
      await leaveApi.apply({
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        reason: reason || undefined
      });
      setIsModalOpen(false);
      setReason('');
      fetchLeaveData();
    } catch (err: any) {
      setModalError(err.response?.data?.detail || 'Failed to submit leave request.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      await leaveApi.approve(id);
      fetchLeaveData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Approval failed.');
    }
  };

  const handleReject = async (id: string) => {
    try {
      await leaveApi.reject(id);
      fetchLeaveData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Rejection failed.');
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await leaveApi.cancel(id);
      fetchLeaveData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Cancellation failed.');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <span className="badge badge-success">Approved</span>;
      case 'PENDING':
        return <span className="badge badge-warning">Pending</span>;
      case 'REJECTED':
        return <span className="badge badge-danger">Rejected</span>;
      case 'CANCELLED':
        return <span className="badge badge-info">Cancelled</span>;
      default:
        return <span className="badge badge-info">{status}</span>;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Leave Management</h1>
          <p className="page-subtitle">Submit leave applications, track balances, and manage approval workflows</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary">
          <Plus size={18} />
          <span>Apply for Leave</span>
        </button>
      </div>

      {/* Leave Balances Grid (if available) */}
      {balances.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
          {balances.map((b) => (
            <div key={b.id} className="glass-panel" style={{ padding: '18px 20px' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                {b.leave_type} Leave
              </span>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', margin: '6px 0' }}>
                {b.remaining_days} <span style={{ fontSize: '0.875rem', color: 'var(--text-dim)', fontWeight: 500 }}>/ {b.allocated_days} days left</span>
              </div>
              <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${(b.used_days / b.allocated_days) * 100}%`,
                  background: 'linear-gradient(90deg, var(--primary), var(--accent-cyan))'
                }}></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filter Bar */}
      <div style={{ display: 'flex', gap: '12px' }}>
        {['', 'PENDING', 'APPROVED', 'REJECTED', 'CANCELLED'].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`btn ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 14px', fontSize: '0.8125rem' }}
          >
            {st || 'All Statuses'}
          </button>
        ))}
      </div>

      {/* Requests Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Employee ID</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    Loading leave applications...
                  </td>
                </tr>
              ) : requests.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No leave requests found.
                  </td>
                </tr>
              ) : (
                requests.map((req) => (
                  <tr key={req.id}>
                    <td style={{ fontWeight: 700, color: '#fff' }}>{req.leave_type}</td>
                    <td style={{ fontFamily: 'monospace', color: 'var(--accent-cyan)' }}>
                      {req.employee_id.substring(0, 8)}...
                    </td>
                    <td>{req.start_date}</td>
                    <td>{req.end_date}</td>
                    <td style={{ color: 'var(--text-muted)', maxWidth: '240px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {req.reason || 'N/A'}
                    </td>
                    <td>{getStatusBadge(req.status)}</td>
                    <td>
                      {req.status === 'PENDING' && (
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button
                            onClick={() => handleApprove(req.id)}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.75rem', color: 'var(--accent-emerald)' }}
                            title="Approve"
                          >
                            <CheckCircle2 size={14} />
                            <span>Approve</span>
                          </button>
                          <button
                            onClick={() => handleReject(req.id)}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.75rem', color: 'var(--accent-rose)' }}
                            title="Reject"
                          >
                            <XCircle size={14} />
                            <span>Reject</span>
                          </button>
                          <button
                            onClick={() => handleCancel(req.id)}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}
                            title="Cancel"
                          >
                            <span>Cancel</span>
                          </button>
                        </div>
                      )}

                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Apply Modal */}
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Submit Leave Request">
        {modalError && (
          <div style={{ padding: '10px 14px', borderRadius: '8px', background: 'rgba(244,63,94,0.15)', color: 'var(--accent-rose)', marginBottom: '16px', fontSize: '0.8125rem' }}>
            {modalError}
          </div>
        )}
        <form onSubmit={handleApply} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label className="input-label">Leave Type</label>
            <select
              value={leaveType}
              onChange={(e) => setLeaveType(e.target.value)}
              className="input-field"
            >
              <option value="Casual">Casual Leave</option>
              <option value="Sick">Sick Leave</option>
              <option value="Earned">Earned Leave</option>
              <option value="Unpaid">Unpaid Leave</option>
            </select>
          </div>

          <div>
            <label className="input-label">Start Date</label>
            <input
              type="date"
              required
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">End Date</label>
            <input
              type="date"
              required
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="input-field"
            />
          </div>

          <div>
            <label className="input-label">Reason / Justification</label>
            <textarea
              rows={3}
              placeholder="Brief explanation for leave request..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="input-field"
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end', marginTop: '12px' }}>
            <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="btn btn-primary">
              {submitting ? 'Submitting...' : 'Submit Request'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
