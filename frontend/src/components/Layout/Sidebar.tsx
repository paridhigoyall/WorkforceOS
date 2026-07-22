import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building2,
  Clock,
  Calendar,
  TrendingUp,
  LogOut,
  Layers
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { label: 'Overview', path: '/', icon: LayoutDashboard },
    { label: 'Employees', path: '/employees', icon: Users },
    { label: 'Departments', path: '/departments', icon: Building2 },
    { label: 'Attendance', path: '/attendance', icon: Clock },
    { label: 'Leave Requests', path: '/leave', icon: Calendar },
    { label: 'Insights & AI', path: '/insights', icon: TrendingUp },
  ];

  return (
    <aside style={{
      width: '260px',
      background: 'rgba(15, 23, 42, 0.95)',
      borderRight: '1px solid var(--glass-border)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      height: '100vh',
      position: 'sticky',
      top: 0
    }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '0 12px 28px 12px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px var(--primary-glow)'
        }}>
          <Layers size={22} color="white" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.5px' }}>WorkforceOS</h1>
          <span style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--accent-cyan)', fontWeight: 700 }}>AI Enterprise</span>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '24px', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                borderRadius: '12px',
                color: isActive ? '#ffffff' : 'var(--text-muted)',
                background: isActive ? 'linear-gradient(90deg, rgba(99, 102, 241, 0.25), rgba(99, 102, 241, 0.05))' : 'transparent',
                borderLeft: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.875rem',
                textDecoration: 'none',
                transition: 'all 0.2s ease'
              })}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* User Info & Logout */}
      <div style={{
        padding: '16px',
        borderRadius: '14px',
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid var(--glass-border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ overflow: 'hidden' }}>
          <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#fff', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user?.email || 'User'}
          </p>
          <span className={`badge ${user?.role === 'admin' ? 'badge-danger' : user?.role === 'hr' ? 'badge-warning' : 'badge-info'}`} style={{ marginTop: '4px', fontSize: '0.65rem' }}>
            {user?.role || 'Staff'}
          </span>
        </div>
        <button
          onClick={logout}
          title="Log out"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};
