import React, { useState, useEffect } from 'react';
import { CheckCircle2, LogOut as CheckOutIcon, Bell, Search } from 'lucide-react';
import { attendanceApi } from '../../api/endpoints';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';

export const TopBar: React.FC = () => {
  const { user } = useAuth();
  const toast = useToast();
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Live clock
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const handleCheckIn = async () => {
    try {
      setLoading(true);
      await attendanceApi.checkIn();
      setIsCheckedIn(true);
      toast.success('You are now clocked in. Have a productive day!', 'Punched In ✓');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Check-in failed. Please try again.', 'Check-In Error');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckOut = async () => {
    try {
      setLoading(true);
      await attendanceApi.checkOut();
      setIsCheckedIn(false);
      toast.success('Your hours have been logged. See you tomorrow!', 'Punched Out ✓');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Check-out failed. Please try again.', 'Check-Out Error');
    } finally {
      setLoading(false);
    }
  };

  const timeStr = currentTime.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });

  const dateStr = currentTime.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });

  const initials = user?.email
    ? user.email.substring(0, 2).toUpperCase()
    : 'WO';

  return (
    <header style={{
      height: '68px',
      borderBottom: '1px solid var(--glass-border)',
      background: 'rgba(7, 11, 20, 0.85)',
      backdropFilter: 'blur(20px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 32px',
      position: 'sticky',
      top: 0,
      zIndex: 50,
    }}>
      {/* Left — Live clock + Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Clock */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{
            fontSize: '1rem',
            fontWeight: 700,
            color: '#fff',
            letterSpacing: '0.5px',
            fontVariantNumeric: 'tabular-nums',
          }}>
            {timeStr}
          </span>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            {dateStr}
          </span>
        </div>

        {/* Divider */}
        <div style={{ width: '1px', height: '32px', background: 'var(--glass-border)' }} />

        {/* API Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '7px',
          padding: '5px 12px',
          borderRadius: '99px',
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.2)',
        }}>
          <span className="status-dot online" />
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-emerald)' }}>
            API Online
          </span>
        </div>

        {/* Check-in status chip */}
        {isCheckedIn && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '7px',
            padding: '5px 12px',
            borderRadius: '99px',
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            fontSize: '0.75rem',
            fontWeight: 700,
            color: 'var(--primary-light)',
          }}>
            <span className="status-dot online" style={{ background: 'var(--primary)' }} />
            On the Clock
          </div>
        )}
      </div>

      {/* Right — Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Search hint */}
        <button
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 14px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--glass-border)',
            borderRadius: '10px',
            color: 'var(--text-dim)',
            fontSize: '0.8125rem',
            cursor: 'pointer',
            transition: 'var(--transition-base)',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.15)';
            (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--glass-border)';
            (e.currentTarget as HTMLElement).style.color = 'var(--text-dim)';
          }}
        >
          <Search size={14} />
          <span>Quick search…</span>
          <kbd style={{
            padding: '1px 6px',
            borderRadius: '5px',
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid var(--glass-border)',
            fontSize: '0.65rem',
            fontFamily: 'monospace',
            color: 'var(--text-dim)',
          }}>
            ⌘K
          </kbd>
        </button>

        {/* Notification bell */}
        <button
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            position: 'relative',
            transition: 'var(--transition-base)',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--glass-border-hover)';
            (e.currentTarget as HTMLElement).style.color = '#fff';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLElement).style.borderColor = 'var(--glass-border)';
            (e.currentTarget as HTMLElement).style.color = 'var(--text-muted)';
          }}
        >
          <Bell size={16} />
          <span style={{
            position: 'absolute',
            top: '6px',
            right: '6px',
            width: '7px',
            height: '7px',
            borderRadius: '50%',
            background: 'var(--accent-rose)',
            border: '1.5px solid var(--bg-dark)',
          }} />
        </button>

        {/* Punch In / Out */}
        {!isCheckedIn ? (
          <button
            onClick={handleCheckIn}
            disabled={loading}
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.8125rem', gap: '7px' }}
          >
            <CheckCircle2 size={15} />
            <span>{loading ? 'Processing…' : 'Punch In'}</span>
          </button>
        ) : (
          <button
            onClick={handleCheckOut}
            disabled={loading}
            className="btn btn-danger"
            style={{ padding: '8px 18px', fontSize: '0.8125rem', gap: '7px' }}
          >
            <CheckOutIcon size={15} />
            <span>{loading ? 'Processing…' : 'Punch Out'}</span>
          </button>
        )}

        {/* Divider */}
        <div style={{ width: '1px', height: '32px', background: 'var(--glass-border)' }} />

        {/* User Avatar */}
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.75rem',
          fontWeight: 800,
          color: '#fff',
          cursor: 'default',
          boxShadow: '0 2px 8px var(--primary-glow)',
          flexShrink: 0,
        }}
          title={user?.email}
        >
          {initials}
        </div>
      </div>
    </header>
  );
};
