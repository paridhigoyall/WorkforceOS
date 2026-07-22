import React, { useState } from 'react';
import { Clock, CheckCircle2, LogOut as CheckOutIcon } from 'lucide-react';
import { attendanceApi } from '../../api/endpoints';

export const TopBar: React.FC = () => {
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleCheckIn = async () => {
    try {
      setLoading(true);
      await attendanceApi.checkIn();
      setIsCheckedIn(true);
      setMessage('Checked in successfully!');
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Check-in failed');
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckOut = async () => {
    try {
      setLoading(true);
      await attendanceApi.checkOut();
      setIsCheckedIn(false);
      setMessage('Checked out successfully!');
      setTimeout(() => setMessage(null), 3000);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Check-out failed');
      setTimeout(() => setMessage(null), 3000);
    } finally {
      setLoading(false);
    }
  };

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });

  return (
    <header style={{
      height: '70px',
      borderBottom: '1px solid var(--glass-border)',
      background: 'rgba(15, 23, 42, 0.6)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 36px',
      position: 'sticky',
      top: 0,
      zIndex: 10
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-muted)' }}>
          {todayStr}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', background: 'rgba(16, 185, 129, 0.1)', padding: '4px 10px', borderRadius: '20px', color: 'var(--accent-emerald)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-emerald)', display: 'inline-block' }}></span>
          API Online
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {message && (
          <span style={{ fontSize: '0.8125rem', color: 'var(--accent-cyan)', fontWeight: 600 }}>
            {message}
          </span>
        )}

        {!isCheckedIn ? (
          <button
            onClick={handleCheckIn}
            disabled={loading}
            className="btn btn-primary"
            style={{ padding: '8px 16px', fontSize: '0.8125rem' }}
          >
            <CheckCircle2 size={16} />
            <span>{loading ? 'Processing...' : 'Punch In'}</span>
          </button>
        ) : (
          <button
            onClick={handleCheckOut}
            disabled={loading}
            className="btn btn-danger"
            style={{ padding: '8px 16px', fontSize: '0.8125rem' }}
          >
            <CheckOutIcon size={16} />
            <span>{loading ? 'Processing...' : 'Punch Out'}</span>
          </button>
        )}
      </div>
    </header>
  );
};
