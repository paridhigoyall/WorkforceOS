import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Building2,
  Clock,
  Calendar,
  DollarSign,
  TrendingUp,
  Shield,
  LogOut,
  Zap,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
  badge?: string;
  badgeColor?: string;
}

const navItems: NavItem[] = [
  { label: 'Overview',      path: '/',            icon: LayoutDashboard },
  { label: 'Employees',     path: '/employees',   icon: Users },
  { label: 'Departments',   path: '/departments', icon: Building2 },
  { label: 'Attendance',    path: '/attendance',  icon: Clock },
  { label: 'Leave',         path: '/leave',       icon: Calendar },
  { label: 'Payroll',       path: '/payroll',     icon: DollarSign, badge: 'New', badgeColor: 'var(--accent-emerald)' },
  { label: 'Insights & AI', path: '/insights',    icon: TrendingUp, badge: 'AI', badgeColor: 'var(--accent-purple)' },
  { label: 'Audit Logs',    path: '/audit-logs',  icon: Shield },
];

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();

  const initials = user?.email
    ? user.email.substring(0, 2).toUpperCase()
    : 'WO';

  const roleConfig = {
    admin: { label: 'Admin',    class: 'badge-danger'  },
    hr:    { label: 'HR',       class: 'badge-warning' },
    staff: { label: 'Staff',    class: 'badge-info'    },
  };
  const role = roleConfig[(user?.role as keyof typeof roleConfig)] ?? { label: 'User', class: 'badge-neutral' };

  return (
    <aside style={{
      width: '260px',
      minWidth: '260px',
      background: 'rgba(7, 11, 20, 0.97)',
      borderRight: '1px solid var(--glass-border)',
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      backdropFilter: 'blur(20px)',
    }}>
      {/* Brand Header */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Logo mark */}
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px var(--primary-glow)',
            flexShrink: 0,
          }}
            className="animate-pulse-glow"
          >
            <Zap size={20} color="white" />
          </div>
          <div>
            <div style={{
              fontSize: '1.125rem',
              fontWeight: 800,
              color: '#fff',
              letterSpacing: '-0.4px',
              lineHeight: 1.2,
            }}>
              WorkforceOS
            </div>
            <div style={{
              fontSize: '0.65rem',
              fontWeight: 700,
              color: 'var(--accent-cyan)',
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
              marginTop: '2px',
            }}>
              AI Enterprise
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Section */}
      <div style={{ padding: '16px 12px', flex: 1, overflowY: 'auto' }}>
        <div style={{
          fontSize: '0.65rem',
          fontWeight: 700,
          color: 'var(--text-dim)',
          letterSpacing: '1px',
          textTransform: 'uppercase',
          padding: '0 10px',
          marginBottom: '8px',
        }}>
          Navigation
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `nav-item${isActive ? ' active' : ''}`
                }
              >
                <Icon size={17} className="nav-icon" />
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge && (
                  <span style={{
                    fontSize: '0.6rem',
                    fontWeight: 800,
                    padding: '2px 6px',
                    borderRadius: '99px',
                    background: `${item.badgeColor}20`,
                    color: item.badgeColor,
                    border: `1px solid ${item.badgeColor}40`,
                    letterSpacing: '0.5px',
                    textTransform: 'uppercase',
                  }}>
                    {item.badge}
                  </span>
                )}
                <ChevronRight
                  size={14}
                  style={{
                    opacity: 0,
                    transition: 'opacity 0.2s, transform 0.2s',
                  }}
                  className="nav-arrow"
                />
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User Profile Footer */}
      <div style={{
        padding: '12px 16px 20px',
        borderTop: '1px solid rgba(255,255,255,0.05)',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 14px',
          borderRadius: '14px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--glass-border)',
          transition: 'var(--transition-base)',
        }}>
          {/* Avatar */}
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.8125rem',
            fontWeight: 800,
            color: '#fff',
            flexShrink: 0,
          }}>
            {initials}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: '#fff',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {user?.email ?? 'User'}
            </div>
            <span className={`badge ${role.class}`} style={{ marginTop: '3px', fontSize: '0.6rem' }}>
              {role.label}
            </span>
          </div>

          <button
            onClick={logout}
            title="Sign out"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              transition: 'color 0.2s, background 0.2s',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.color = 'var(--accent-rose)';
              (e.currentTarget as HTMLElement).style.background = 'rgba(244,63,94,0.1)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.color = 'var(--text-dim)';
              (e.currentTarget as HTMLElement).style.background = 'none';
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
};
