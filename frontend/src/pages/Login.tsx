import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Lock, Mail, UserPlus, LogIn, Eye, EyeOff, ShieldCheck, KeyRound, ArrowLeft } from 'lucide-react';
import { authApi } from '../api/endpoints';
import { useAuth } from '../context/useAuth';

/* Floating particle config */
const PARTICLES = Array.from({ length: 30 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 3 + 1,
  duration: Math.random() * 10 + 8,
  delay: Math.random() * 5,
  opacity: Math.random() * 0.4 + 0.1,
}));

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [isRegistering, setIsRegistering] = useState(false);
  const [isMfaStep, setIsMfaStep] = useState(false);
  const [mfaChallengeToken, setMfaChallengeToken] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState('');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('staff');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const emailRef = useRef<HTMLInputElement>(null);
  const mfaInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isMfaStep) {
      mfaInputRef.current?.focus();
    } else {
      emailRef.current?.focus();
    }
  }, [isMfaStep]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isRegistering) {
        const res = await authApi.register({ email, password, role });
        login(res.access_token, res.user, res.refresh_token);
        navigate('/');
      } else if (isMfaStep && mfaChallengeToken) {
        const verifyRes = await authApi.verifyMfa(mfaChallengeToken, mfaCode);
        if (verifyRes.access_token) {
          localStorage.setItem('workforce_token', verifyRes.access_token);
          const userRes = await authApi.getMe();
          login(verifyRes.access_token, userRes, verifyRes.refresh_token);
          navigate('/');
        }
      } else {
        const tokenRes = await authApi.login(email, password);
        if (tokenRes.mfa_required && tokenRes.mfa_token) {
          setIsMfaStep(true);
          setMfaChallengeToken(tokenRes.mfa_token);
          setError(null);
        } else if (tokenRes.access_token) {
          localStorage.setItem('workforce_token', tokenRes.access_token);
          const userRes = await authApi.getMe();
          login(tokenRes.access_token, userRes, tokenRes.refresh_token);
          navigate('/');
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setIsMfaStep(false);
    setMfaChallengeToken(null);
    setMfaCode('');
    setError(null);
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
      background: 'radial-gradient(ellipse at 25% 20%, rgba(184,155,251,0.14) 0%, transparent 50%), radial-gradient(ellipse at 75% 80%, rgba(217,155,108,0.12) 0%, transparent 50%), var(--bg-dark)',
    }}>
      {/* Background particles */}
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        {PARTICLES.map(p => (
          <div
            key={p.id}
            style={{
              position: 'absolute',
              left: `${p.x}%`,
              top: `${p.y}%`,
              width: `${p.size}px`,
              height: `${p.size}px`,
              borderRadius: '50%',
              background: p.id % 3 === 0 ? 'var(--primary)' : p.id % 3 === 1 ? 'var(--wood-accent)' : 'var(--accent-lilac)',
              opacity: p.opacity,
              animation: `float ${p.duration}s ${p.delay}s ease-in-out infinite`,
            }}
          />
        ))}
        {/* Grid lines */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(217,155,108,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(184,155,251,0.03) 1px, transparent 1px)
          `,
          backgroundSize: '64px 64px',
        }} />
      </div>

      {/* Card */}
      <div
        className="animate-scaleIn"
        style={{
          width: '100%',
          maxWidth: '448px',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div style={{
          background: 'rgba(32, 23, 20, 0.94)',
          backdropFilter: 'blur(24px)',
          border: '1px solid var(--glass-border-hover)',
          borderRadius: 'var(--radius-xl)',
          boxShadow: '0 32px 64px rgba(15,11,9,0.7), 0 0 48px rgba(184,155,251,0.15), inset 0 1px 0 rgba(255,255,255,0.08)',
          padding: '40px',
        }}>
          {/* Brand */}
          <div style={{ textAlign: 'center', marginBottom: '36px' }}>
            <div style={{
              width: '60px',
              height: '60px',
              borderRadius: '18px',
              background: 'linear-gradient(135deg, var(--primary), var(--wood-accent))',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 32px var(--primary-glow)',
              marginBottom: '20px',
            }}
              className="animate-float"
            >
              <Zap size={30} color="white" />
            </div>
            <h1 style={{
              fontSize: '1.875rem',
              fontWeight: 800,
              color: '#fff',
              letterSpacing: '-0.5px',
              lineHeight: 1.2,
            }}>
              WorkforceOS
            </h1>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '8px' }}>
              {isRegistering ? 'Create your workspace account' : 'Sign in to your enterprise workspace'}
            </p>
          </div>

          {/* Security badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '7px',
            marginBottom: '28px',
            padding: '8px 16px',
            borderRadius: '99px',
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.15)',
            color: 'var(--accent-emerald)',
            fontSize: '0.75rem',
            fontWeight: 700,
          }}>
            <ShieldCheck size={14} />
            <span>End-to-end encrypted session</span>
          </div>

          {/* Error alert */}
          {error && (
            <div style={{
              padding: '13px 16px',
              borderRadius: '12px',
              background: 'rgba(244, 63, 94, 0.1)',
              border: '1px solid rgba(244, 63, 94, 0.25)',
              color: '#fb7185',
              fontSize: '0.8125rem',
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              animation: 'fadeInUp 0.3s ease',
            }}>
              <span>⚠</span>
              {error}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {isMfaStep ? (
              /* MFA TOTP Step */
              <div style={{ animation: 'fadeInUp 0.3s ease', display: 'flex', flexDirection: 'column', gap: '18px' }}>
                <div style={{
                  padding: '16px',
                  borderRadius: '12px',
                  background: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  textAlign: 'center',
                }}>
                  <KeyRound size={28} color="var(--primary)" style={{ margin: '0 auto 8px' }} />
                  <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                    Two-Factor Authentication
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                    Enter the 6-digit verification code from your authenticator app.
                  </div>
                </div>

                <div>
                  <label className="input-label">Authentication Code</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      ref={mfaInputRef}
                      id="login-mfa-code"
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={6}
                      required
                      value={mfaCode}
                      onChange={e => setMfaCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="000000"
                      className="input-field"
                      style={{
                        paddingLeft: '16px',
                        fontSize: '1.25rem',
                        letterSpacing: '6px',
                        textAlign: 'center',
                        fontWeight: 700,
                      }}
                      autoComplete="one-time-code"
                    />
                  </div>
                </div>

                <button
                  id="login-mfa-submit"
                  type="submit"
                  disabled={loading || mfaCode.length !== 6}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '13px', fontSize: '0.9375rem', marginTop: '4px' }}
                >
                  {loading ? (
                    <span className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                  ) : (
                    <>
                      <ShieldCheck size={18} />
                      <span>Verify & Continue</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={handleBackToLogin}
                  style={{
                    background: 'none',
                    border: 'none',
                    color: 'var(--text-muted)',
                    fontSize: '0.8125rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                  }}
                >
                  <ArrowLeft size={14} />
                  <span>Cancel & Back to Email Login</span>
                </button>
              </div>
            ) : (
              /* Standard Email + Password Fields */
              <>
                {/* Email */}
                <div>
                  <label className="input-label">Email Address</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      ref={emailRef}
                      id="login-email"
                      type="email"
                      required
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      placeholder="name@company.com"
                      className="input-field"
                      style={{ paddingLeft: '42px' }}
                      autoComplete="email"
                    />
                    <Mail size={16} color="var(--text-dim)" style={{
                      position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none',
                    }} />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <label className="input-label">Password</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      id="login-password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder="••••••••••"
                      className="input-field"
                      style={{ paddingLeft: '42px', paddingRight: '42px' }}
                      autoComplete={isRegistering ? 'new-password' : 'current-password'}
                    />
                    <Lock size={16} color="var(--text-dim)" style={{
                      position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none',
                    }} />
                    <button
                      type="button"
                      tabIndex={-1}
                      onClick={() => setShowPassword(v => !v)}
                      style={{
                        position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)',
                        background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-dim)',
                        display: 'flex', alignItems: 'center', padding: '4px',
                      }}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Role selector (register only) */}
                {isRegistering && (
                  <div style={{ animation: 'fadeInUp 0.3s ease' }}>
                    <label className="input-label">Account Role</label>
                    <select
                      value={role}
                      onChange={e => setRole(e.target.value)}
                      className="input-field"
                    >
                      <option value="admin">Administrator</option>
                      <option value="hr">HR Manager</option>
                      <option value="staff">Staff Member</option>
                    </select>
                  </div>
                )}

                {/* Submit */}
                <button
                  id="login-submit"
                  type="submit"
                  disabled={loading}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '13px', fontSize: '0.9375rem', marginTop: '6px' }}
                >
                  {loading ? (
                    <span className="spinner" style={{ width: '18px', height: '18px', borderWidth: '2px' }} />
                  ) : (
                    <>
                      {isRegistering ? <UserPlus size={17} /> : <LogIn size={17} />}
                      <span>{isRegistering ? 'Create Account' : 'Sign In to Workspace'}</span>
                    </>
                  )}
                </button>
              </>
            )}
          </form>

          {/* Toggle */}
          {!isMfaStep && (
            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <button
                onClick={() => { setIsRegistering(v => !v); setError(null); }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-cyan)',
                  fontSize: '0.8125rem',
                  cursor: 'pointer',
                  fontWeight: 600,
                  transition: 'opacity 0.2s',
                }}
                onMouseEnter={e => (e.currentTarget.style.opacity = '0.75')}
                onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
              >
                {isRegistering ? '← Back to Sign In' : 'Need an account? Register →'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
