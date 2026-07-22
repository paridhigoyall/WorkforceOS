import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: string;
  trend?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'var(--primary)',
  trend
}) => {
  return (
    <div className="glass-panel" style={{ padding: '20px 24px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          {title}
        </span>
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '10px',
          background: `${color}18`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: color
        }}>
          <Icon size={20} />
        </div>
      </div>

      <div style={{ fontSize: '1.875rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.5px' }}>
        {value}
      </div>

      {(subtitle || trend) && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px', fontSize: '0.75rem' }}>
          {trend && (
            <span style={{ color: 'var(--accent-emerald)', fontWeight: 700 }}>
              {trend}
            </span>
          )}
          {subtitle && (
            <span style={{ color: 'var(--text-dim)' }}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
