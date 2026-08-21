import React, { useEffect, useState } from 'react';
import { Filter, Eye, RefreshCw } from 'lucide-react';

import { auditLogsApi } from '../api/endpoints';
import type { AuditLogEntry } from '../types';
import { Modal } from '../components/UI/Modal';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [targetFilter, setTargetFilter] = useState<string>('');

  // Selected JSON Inspect Modal
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await auditLogsApi.list({
        action: actionFilter || undefined,
        target_type: targetFilter || undefined,
        limit: 100
      });
      setLogs(data.items);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter, targetFilter]);

  const getActionBadge = (action: string) => {
    if (action.includes('ONBOARD') || action.includes('CREATE') || action.includes('APPROVE')) {
      return <span className="badge badge-success">{action}</span>;
    }
    if (action.includes('UPDATE') || action.includes('EDIT')) {
      return <span className="badge badge-info">{action}</span>;
    }
    if (action.includes('OFFBOARD') || action.includes('DELETE') || action.includes('REJECT')) {
      return <span className="badge badge-danger">{action}</span>;
    }
    if (action.includes('PAYROLL') || action.includes('GENERATE')) {
      return <span className="badge badge-warning">{action}</span>;
    }
    return <span className="badge badge-info">{action}</span>;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">System Audit Logs</h1>
          <p className="page-subtitle">Immutable security trail of all state-altering write operations and business events</p>
        </div>
        <button onClick={fetchLogs} className="btn btn-secondary" style={{ padding: '8px 14px', fontSize: '0.8125rem' }}>
          <RefreshCw size={16} />
          <span>Refresh Logs</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="var(--text-muted)" />
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="input-field"
            style={{ width: '200px' }}
          >
            <option value="">All Actions</option>
            <option value="ONBOARD_EMPLOYEE">ONBOARD_EMPLOYEE</option>
            <option value="UPDATE_EMPLOYEE">UPDATE_EMPLOYEE</option>
            <option value="OFFBOARD_EMPLOYEE">OFFBOARD_EMPLOYEE</option>
            <option value="CREATE_DEPARTMENT">CREATE_DEPARTMENT</option>
            <option value="UPDATE_DEPARTMENT">UPDATE_DEPARTMENT</option>
            <option value="DELETE_DEPARTMENT">DELETE_DEPARTMENT</option>
            <option value="APPROVE_LEAVE">APPROVE_LEAVE</option>
            <option value="REJECT_LEAVE">REJECT_LEAVE</option>
            <option value="GENERATE_PAYROLL">GENERATE_PAYROLL</option>
            <option value="APPROVE_PAYROLL">APPROVE_PAYROLL</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>Entity Type:</span>
          <select
            value={targetFilter}
            onChange={(e) => setTargetFilter(e.target.value)}
            className="input-field"
            style={{ width: '180px' }}
          >
            <option value="">All Entities</option>
            <option value="employees">employees</option>
            <option value="departments">departments</option>
            <option value="leave_requests">leave_requests</option>
            <option value="payroll_periods">payroll_periods</option>
          </select>
        </div>

        {(actionFilter || targetFilter) && (
          <button
            onClick={() => { setActionFilter(''); setTargetFilter(''); }}
            className="btn btn-secondary"
            style={{ padding: '8px 14px', fontSize: '0.8125rem' }}
          >
            Clear Filters
          </button>
        )}

        <div style={{ marginLeft: 'auto', fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          Total Audit Records: <span style={{ color: '#fff', fontWeight: 700 }}>{total}</span>
        </div>
      </div>

      {/* Logs Table */}
      <div className="glass-panel" style={{ overflow: 'hidden' }}>
        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Operator (User)</th>
                <th>Action</th>
                <th>Target Entity</th>
                <th>Target ID</th>
                <th>Change Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    Loading audit trail...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                    No audit log records found matching filters.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id}>
                    <td style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td style={{ fontWeight: 600, color: '#fff' }}>
                      {log.user_email || log.user_id.substring(0, 8)}
                    </td>
                    <td>{getActionBadge(log.action)}</td>
                    <td style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>
                      {log.target_type}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: 'var(--text-dim)' }}>
                      {log.target_id.substring(0, 8)}...
                    </td>
                    <td>
                      {log.details ? (
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '0.75rem', color: 'var(--accent-cyan)' }}
                        >
                          <Eye size={14} />
                          <span>Inspect Payload</span>
                        </button>
                      ) : (
                        <span style={{ color: 'var(--text-dim)', fontSize: '0.8125rem' }}>No Payload</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Payload Inspection Modal */}
      <Modal
        isOpen={!!selectedLog}
        onClose={() => setSelectedLog(null)}
        title={`Audit Event Details: ${selectedLog?.action}`}
      >
        {selectedLog && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.8125rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Operator: </span>
                <span style={{ fontWeight: 700, color: '#fff' }}>{selectedLog.user_email || selectedLog.user_id}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Target Entity: </span>
                <span style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{selectedLog.target_type}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Target ID: </span>
                <span style={{ fontFamily: 'monospace', color: '#fff' }}>{selectedLog.target_id}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Timestamp: </span>
                <span style={{ color: '#fff' }}>{new Date(selectedLog.created_at).toLocaleString()}</span>
              </div>
            </div>

            <div style={{ marginTop: '8px' }}>
              <label className="input-label">JSON Change Payload</label>
              <pre style={{
                background: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid var(--glass-border)',
                borderRadius: '10px',
                padding: '16px',
                color: 'var(--accent-emerald)',
                fontSize: '0.8125rem',
                fontFamily: 'monospace',
                overflowX: 'auto',
                maxHeight: '300px'
              }}>
                {JSON.stringify(selectedLog.details, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
