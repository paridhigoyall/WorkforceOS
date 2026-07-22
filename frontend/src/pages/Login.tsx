import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layers, Lock, Mail, UserPlus, LogIn } from 'lucide-react';
import { authApi } from '../api/endpoints';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);

  const [email, setEmail] = useState('admin@workforce.os');
  const [password, setPassword] = useState('Admin123!');
  const [role, setRole] = useState('admin');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegistering) {
        const res = await authApi.register({ email, password, role });
        login(res.access_token, res.user);
      } else {
        const tokenRes = await authApi.login(email, password);
        localStorage.setItem('workforce_token', tokenRes.access_token);
        const userRes = await authApi.getMe();
        login(tokenRes.access_token, userRes);
      }
      navigate('/');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      background: 'radial-gradient(circle at 50% 30%, #1e1b4b 0%, #090d16 70%)'
    }}>
      <div className="glass-panel" style={{
        width: '100%',
        maxWidth: '440px',
        padding: '40px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)'
      }}>
        {/* Brand */}
        <div style={{ textAlignment: 'center', textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '52px',
            height: '52px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, var(--primary), var(--accent-purple))',
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 24px var(--primary-glow)',
            marginBottom: '16px'
          }}>
            <Layers size={28} color="white" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.5px' }}>
            WorkforceOS
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {isRegistering ? 'Create your workforce account' : 'Sign in to access your workspace'}
          </p>
        </div>

        {error && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '10px',
            background: 'rgba(244, 63, 94, 0.12)',
            border: '1px solid rgba(244, 63, 94, 0.3)',
            color: 'var(--accent-rose)',
            fontSize: '0.8125rem',
            marginBottom: '20px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label className="input-label">Email Address</label>
            <div style={{ position: 'relative' }}>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@company.com"
                className="input-field"
                style={{ paddingLeft: '40px' }}
              />
              <Mail size={18} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          <div>
            <label className="input-label">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="input-field"
                style={{ paddingLeft: '40px' }}
              />
              <Lock size={18} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            </div>
          </div>

          {isRegistering && (
            <div>
              <label className="input-label">Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="input-field"
              >
                <option value="admin">Administrator</option>
                <option value="hr">HR Manager</option>
                <option value="staff">Staff Member</option>
              </select>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '12px', marginTop: '8px', fontSize: '0.9375rem' }}
          >
            {isRegistering ? <UserPlus size={18} /> : <LogIn size={18} />}
            <span>{loading ? 'Authenticating...' : isRegistering ? 'Register Account' : 'Sign In'}</span>
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center' }}>
          <button
            onClick={() => setIsRegistering(!isRegistering)}
            style={{ background: 'none', border: 'none', color: 'var(--accent-cyan)', fontSize: '0.8125rem', cursor: 'pointer', fontWeight: 600 }}
          >
            {isRegistering ? 'Already have an account? Sign in' : 'Need an account? Register here'}
          </button>
        </div>
      </div>
    </div>
  );
};
