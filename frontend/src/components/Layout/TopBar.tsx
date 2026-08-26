import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  LogOut as CheckOutIcon,
  Bell,
  Search,
  Shield,
  ShieldCheck,
  ShieldAlert,
  KeyRound,
  Calendar,
  CreditCard,
  Clock,
  Info,
  X,
  Copy,
} from 'lucide-react';
import { attendanceApi, notificationsApi, authApi } from '../../api/endpoints';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import type { Notification, MFASetupResponse } from '../../types';

export const TopBar: React.FC = () => {
  const navigate = useNavigate();
  const { user, updateUser } = useAuth();
  const toast = useToast();

  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Notification states
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isNotifOpen, setIsNotifOpen] = useState<boolean>(false);
  const notifRef = useRef<HTMLDivElement>(null);

  // Security / MFA Modal states
  const [isSecurityModalOpen, setIsSecurityModalOpen] = useState(false);
  const [mfaSetupData, setMfaSetupData] = useState<MFASetupResponse | null>(null);
  const [mfaPassword, setMfaPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [mfaActionLoading, setMfaActionLoading] = useState(false);

  // Live clock
  useEffect(() => {
    const interval = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch notifications & unread count
  const fetchNotifications = async () => {
    try {
      const [countRes, listRes] = await Promise.all([
        notificationsApi.getUnreadCount(),
        notificationsApi.list({ limit: 12 }),
      ]);
      setUnreadCount(countRes.unread_count);
      setNotifications(listRes);
    } catch {
      // Background poll failure
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000); // poll every 15s
    return () => clearInterval(interval);
  }, []);

  // Close notif popover on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setIsNotifOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
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

  const handleMarkAllNotificationsRead = async () => {
    try {
      await notificationsApi.markAllAsRead();
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      toast.info('All notifications marked as read');
    } catch {
      toast.error('Failed to mark all notifications as read');
    }
  };

  const handleNotificationClick = async (notif: Notification) => {
    if (!notif.is_read) {
      try {
        await notificationsApi.markAsRead(notif.id);
        setUnreadCount(prev => Math.max(0, prev - 1));
        setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
      } catch {
        // Continue navigation
      }
    }
    if (notif.link) {
      setIsNotifOpen(false);
      navigate(notif.link);
    }
  };

  const handleStartMfaSetup = async () => {
    try {
      setMfaActionLoading(true);
      const res = await authApi.setupMfa();
      setMfaSetupData(res);
      setMfaCode('');
      setMfaPassword('');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to initialize MFA setup.');
    } finally {
      setMfaActionLoading(false);
    }
  };

  const handleConfirmEnableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setMfaActionLoading(true);
      await authApi.enableMfa({ password: mfaPassword, code: mfaCode });
      if (user) {
        updateUser({ ...user, is_mfa_enabled: true });
      }
      setMfaSetupData(null);
      setMfaCode('');
      setMfaPassword('');
      toast.success('Two-factor authentication is now active on your account.', 'MFA Enabled 🔒');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid password or verification code.');
    } finally {
      setMfaActionLoading(false);
    }
  };

  const handleConfirmDisableMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setMfaActionLoading(true);
      await authApi.disableMfa({ password: mfaPassword, code: mfaCode });
      if (user) {
        updateUser({ ...user, is_mfa_enabled: false });
      }
      setMfaCode('');
      setMfaPassword('');
      toast.warning('Two-factor authentication has been disabled.', 'MFA Deactivated');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid password or verification code.');
    } finally {
      setMfaActionLoading(false);
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

  const getNotifIcon = (type: string) => {
    switch (type) {
      case 'leave':
        return <Calendar size={15} color="var(--accent-purple)" />;
      case 'payroll':
        return <CreditCard size={15} color="var(--accent-emerald)" />;
      case 'attendance':
        return <Clock size={15} color="var(--accent-amber)" />;
      default:
        return <Info size={15} color="var(--accent-cyan)" />;
    }
  };

  return (
    <>
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
            onClick={() => navigate('/insights')}
          >
            <Search size={14} />
            <span>Search workspace…</span>
            <kbd style={{
              padding: '1px 6px',
              borderRadius: '5px',
              background: 'rgba(255,255,255,0.06)',
              border: '1px solid var(--glass-border)',
              fontSize: '0.65rem',
              fontFamily: 'monospace',
              color: 'var(--text-dim)',
            }}>
              /
            </kbd>
          </button>

          {/* Notification Center */}
          <div ref={notifRef} style={{ position: 'relative' }}>
            <button
              id="topbar-notifications-btn"
              onClick={() => setIsNotifOpen(v => !v)}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: isNotifOpen ? 'rgba(99,102,241,0.15)' : 'rgba(255,255,255,0.04)',
                border: isNotifOpen ? '1px solid var(--primary)' : '1px solid var(--glass-border)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: isNotifOpen ? '#fff' : 'var(--text-muted)',
                position: 'relative',
                transition: 'var(--transition-base)',
              }}
              title="Notifications"
            >
              <Bell size={16} />
              {unreadCount > 0 && (
                <span style={{
                  position: 'absolute',
                  top: '-4px',
                  right: '-4px',
                  minWidth: '18px',
                  height: '18px',
                  padding: '0 4px',
                  borderRadius: '99px',
                  background: 'var(--accent-rose)',
                  color: '#fff',
                  fontSize: '0.6875rem',
                  fontWeight: 800,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 0 8px rgba(244,63,94,0.6)',
                }}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {/* Notification Dropdown Menu */}
            {isNotifOpen && (
              <div
                className="animate-scaleIn"
                style={{
                  position: 'absolute',
                  top: '46px',
                  right: 0,
                  width: '360px',
                  maxHeight: '440px',
                  background: 'rgba(10, 15, 28, 0.96)',
                  backdropFilter: 'blur(24px)',
                  border: '1px solid var(--glass-border-hover)',
                  borderRadius: 'var(--radius-lg)',
                  boxShadow: '0 20px 48px rgba(0,0,0,0.6), 0 0 32px rgba(99,102,241,0.15)',
                  display: 'flex',
                  flexDirection: 'column',
                  overflow: 'hidden',
                  zIndex: 100,
                }}
              >
                {/* Header */}
                <div style={{
                  padding: '14px 18px',
                  borderBottom: '1px solid var(--glass-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  background: 'rgba(255,255,255,0.02)',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#fff' }}>Notifications</span>
                    {unreadCount > 0 && (
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '99px',
                        background: 'rgba(99,102,241,0.15)',
                        color: 'var(--primary-light)',
                        fontSize: '0.6875rem',
                        fontWeight: 700,
                      }}>
                        {unreadCount} new
                      </span>
                    )}
                  </div>
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllNotificationsRead}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--accent-cyan)',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                      }}
                    >
                      Mark all read
                    </button>
                  )}
                </div>

                {/* Notification List */}
                <div style={{ overflowY: 'auto', flex: 1, padding: '6px' }}>
                  {notifications.length === 0 ? (
                    <div style={{ padding: '36px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                      <CheckCircle2 size={28} color="var(--text-dim)" style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                      <div style={{ fontSize: '0.8125rem', fontWeight: 600 }}>All caught up!</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>No new notifications at this time.</div>
                    </div>
                  ) : (
                    notifications.map(n => (
                      <div
                        key={n.id}
                        onClick={() => handleNotificationClick(n)}
                        style={{
                          padding: '12px 14px',
                          borderRadius: '8px',
                          marginBottom: '4px',
                          cursor: 'pointer',
                          background: n.is_read ? 'transparent' : 'rgba(99,102,241,0.06)',
                          borderLeft: n.is_read ? '3px solid transparent' : '3px solid var(--primary)',
                          transition: 'background 0.2s',
                          display: 'flex',
                          gap: '12px',
                        }}
                        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
                        onMouseLeave={e => (e.currentTarget.style.background = n.is_read ? 'transparent' : 'rgba(99,102,241,0.06)')}
                      >
                        <div style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '8px',
                          background: 'rgba(255,255,255,0.05)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          marginTop: '2px',
                        }}>
                          {getNotifIcon(n.type)}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '0.8125rem', fontWeight: n.is_read ? 600 : 700, color: '#fff', marginBottom: '2px' }}>
                            {n.title}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
                            {n.message}
                          </div>
                          <div style={{ fontSize: '0.6875rem', color: 'var(--text-dim)', marginTop: '4px' }}>
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

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

          {/* User Avatar with Security settings trigger */}
          <button
            onClick={() => setIsSecurityModalOpen(true)}
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))',
              border: user?.is_mfa_enabled ? '2px solid var(--accent-emerald)' : '1px solid var(--glass-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.75rem',
              fontWeight: 800,
              color: '#fff',
              cursor: 'pointer',
              boxShadow: '0 2px 8px var(--primary-glow)',
              flexShrink: 0,
              position: 'relative',
            }}
            title="Account & MFA Security Settings"
          >
            {initials}
            {user?.is_mfa_enabled && (
              <span style={{
                position: 'absolute',
                bottom: '-3px',
                right: '-3px',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                background: 'var(--accent-emerald)',
                border: '1.5px solid var(--bg-dark)',
              }} />
            )}
          </button>
        </div>
      </header>

      {/* Security & MFA Settings Modal */}
      {isSecurityModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.75)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          padding: '20px',
        }}>
          <div
            className="animate-scaleIn"
            style={{
              width: '100%',
              maxWidth: '520px',
              background: 'rgba(10, 15, 28, 0.98)',
              border: '1px solid var(--glass-border-hover)',
              borderRadius: 'var(--radius-xl)',
              boxShadow: '0 32px 64px rgba(0,0,0,0.8), 0 0 48px rgba(99,102,241,0.15)',
              padding: '32px',
              position: 'relative',
            }}
          >
            {/* Close */}
            <button
              onClick={() => { setIsSecurityModalOpen(false); setMfaSetupData(null); }}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
              }}
            >
              <X size={20} />
            </button>

            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '24px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '12px',
                background: 'rgba(99,102,241,0.12)',
                border: '1px solid rgba(99,102,241,0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <Shield size={22} color="var(--primary)" />
              </div>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', margin: 0 }}>
                  Account Security
                </h3>
                <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: 0 }}>
                  Manage multi-factor authentication (MFA) and access security.
                </p>
              </div>
            </div>

            {/* User Profile Card */}
            <div style={{
              padding: '16px',
              borderRadius: '12px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px solid var(--glass-border)',
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#fff' }}>{user?.email}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Role: <span style={{ color: 'var(--accent-cyan)', fontWeight: 600, textTransform: 'capitalize' }}>{user?.role}</span>
                </div>
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '4px 10px',
                borderRadius: '99px',
                fontSize: '0.75rem',
                fontWeight: 700,
                background: user?.is_mfa_enabled ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
                color: user?.is_mfa_enabled ? 'var(--accent-emerald)' : '#fb7185',
                border: `1px solid ${user?.is_mfa_enabled ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)'}`,
              }}>
                {user?.is_mfa_enabled ? <ShieldCheck size={14} /> : <ShieldAlert size={14} />}
                <span>{user?.is_mfa_enabled ? '2FA Enabled' : '2FA Disabled'}</span>
              </div>
            </div>

            {/* MFA Setup / Configuration Flow */}
            {!user?.is_mfa_enabled ? (
              mfaSetupData ? (
                /* Step 2: Confirm Code with Secret */
                <form onSubmit={handleConfirmEnableMfa} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{
                    padding: '14px',
                    borderRadius: '10px',
                    background: 'rgba(99,102,241,0.08)',
                    border: '1px solid rgba(99,102,241,0.2)',
                  }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                      Add this secret key to Google Authenticator or your TOTP app:
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: 'rgba(0,0,0,0.4)',
                      borderRadius: '8px',
                      fontFamily: 'monospace',
                      color: 'var(--accent-cyan)',
                      fontSize: '0.9375rem',
                      fontWeight: 700,
                    }}>
                      <span>{mfaSetupData.secret}</span>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(mfaSetupData.secret);
                          toast.info('Secret key copied to clipboard');
                        }}
                        style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                        title="Copy Key"
                      >
                        <Copy size={16} />
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="input-label">Account Password</label>
                    <input
                      type="password"
                      required
                      value={mfaPassword}
                      onChange={e => setMfaPassword(e.target.value)}
                      placeholder="Confirm your password"
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="input-label">6-Digit Authenticator Code</label>
                    <input
                      type="text"
                      maxLength={6}
                      required
                      value={mfaCode}
                      onChange={e => setMfaCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="000000"
                      className="input-field"
                      style={{ fontSize: '1.125rem', letterSpacing: '4px', textAlign: 'center', fontWeight: 700 }}
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '10px', marginTop: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setMfaSetupData(null)}
                      className="btn btn-secondary"
                      style={{ flex: 1 }}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={mfaActionLoading || mfaCode.length !== 6}
                      className="btn btn-primary"
                      style={{ flex: 1 }}
                    >
                      {mfaActionLoading ? 'Activating…' : 'Activate 2FA'}
                    </button>
                  </div>
                </form>
              ) : (
                /* Step 1: Prompt to enable */
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '20px' }}>
                    Enhance your account with Time-Based One-Time Password (TOTP) two-factor authentication via Google Authenticator, Authy, or 1Password.
                  </p>
                  <button
                    onClick={handleStartMfaSetup}
                    disabled={mfaActionLoading}
                    className="btn btn-primary"
                    style={{ width: '100%', padding: '12px' }}
                  >
                    <KeyRound size={16} />
                    <span>{mfaActionLoading ? 'Preparing Setup…' : 'Enable Two-Factor Authentication'}</span>
                  </button>
                </div>
              )
            ) : (
              /* Disable MFA Flow */
              <form onSubmit={handleConfirmDisableMfa} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{
                  padding: '14px',
                  borderRadius: '10px',
                  background: 'rgba(244,63,94,0.08)',
                  border: '1px solid rgba(244,63,94,0.2)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-muted)',
                }}>
                  Disabling 2FA reduces account security. Enter your password and current authenticator code to confirm.
                </div>

                <div>
                  <label className="input-label">Account Password</label>
                  <input
                    type="password"
                    required
                    value={mfaPassword}
                    onChange={e => setMfaPassword(e.target.value)}
                    placeholder="Enter password"
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="input-label">Current 6-Digit Code</label>
                  <input
                    type="text"
                    maxLength={6}
                    required
                    value={mfaCode}
                    onChange={e => setMfaCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    className="input-field"
                    style={{ fontSize: '1.125rem', letterSpacing: '4px', textAlign: 'center', fontWeight: 700 }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={mfaActionLoading || mfaCode.length !== 6}
                  className="btn btn-danger"
                  style={{ width: '100%', padding: '12px', marginTop: '6px' }}
                >
                  {mfaActionLoading ? 'Disabling…' : 'Deactivate Two-Factor Authentication'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
};

