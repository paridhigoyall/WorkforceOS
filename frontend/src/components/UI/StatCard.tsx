import React, { useEffect, useRef, useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: string;
  trend?: string;
  trendType?: 'up' | 'down' | 'neutral';
  animateValue?: boolean;
  delay?: number;
}

function useCountUp(target: number, duration = 900, trigger = true) {
  const [current, setCurrent] = useState(0);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    if (!trigger) return;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setCurrent(Math.round(eased * target));
      if (progress < 1) frame.current = requestAnimationFrame(tick);
    };
    frame.current = requestAnimationFrame(tick);
    return () => { if (frame.current) cancelAnimationFrame(frame.current); };
  }, [target, duration, trigger]);

  return current;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'var(--primary)',
  trend,
  trendType = 'neutral',
  animateValue = true,
  delay = 0,
}) => {
  const isNumeric = typeof value === 'number';
  const numericVal = useCountUp(isNumeric ? value : 0, 900, isNumeric && animateValue);

  const TrendIcon =
    trendType === 'up' ? TrendingUp :
    trendType === 'down' ? TrendingDown :
    Minus;

  const trendColor =
    trendType === 'up' ? 'var(--accent-emerald)' :
    trendType === 'down' ? 'var(--accent-rose)' :
    'var(--text-muted)';

  return (
    <div
      className="glass-panel animate-fadeInUp"
      style={{
        padding: '22px 24px',
        position: 'relative',
        overflow: 'hidden',
        animationDelay: `${delay}s`,
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'default',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.transform = 'translateY(-3px)';
        (e.currentTarget as HTMLElement).style.boxShadow = `0 12px 36px rgba(0,0,0,0.4), 0 0 24px ${color}30`;
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
        (e.currentTarget as HTMLElement).style.boxShadow = '';
      }}
    >
      {/* Accent top bar */}
      <div
        className="stat-card-accent"
        style={{ background: `linear-gradient(90deg, ${color}, transparent)` }}
      />

      {/* Faint icon watermark */}
      <div style={{
        position: 'absolute',
        right: '-8px',
        bottom: '-8px',
        opacity: 0.04,
        transform: 'scale(2.5)',
        color: color,
        pointerEvents: 'none',
      }}>
        <Icon size={48} />
      </div>

      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <span style={{
          fontSize: '0.7rem',
          fontWeight: 800,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
        }}>
          {title}
        </span>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '11px',
          background: `${color}15`,
          border: `1px solid ${color}25`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: color,
        }}>
          <Icon size={18} />
        </div>
      </div>

      {/* Value */}
      <div style={{
        fontSize: '2rem',
        fontWeight: 800,
        color: '#ffffff',
        letterSpacing: '-0.8px',
        lineHeight: 1,
        animation: 'countUp 0.6s ease both',
      }}>
        {isNumeric && animateValue ? numericVal : value}
      </div>

      {/* Footer */}
      {(subtitle || trend) && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginTop: '10px',
          fontSize: '0.78rem',
        }}>
          {trend && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', color: trendColor, fontWeight: 700 }}>
              <TrendIcon size={13} />
              <span>{trend}</span>
            </div>
          )}
          {subtitle && (
            <span style={{ color: 'var(--text-dim)', lineHeight: 1.4 }}>{subtitle}</span>
          )}
        </div>
      )}
    </div>
  );
};
