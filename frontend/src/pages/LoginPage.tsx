import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login, user } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (user) {
    return <Navigate to={user.onboarding_completed ? '/dashboard' : '/onboarding'} replace />
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const done = await login(email, password)
      navigate(done ? '/dashboard' : '/onboarding')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Login to continue">
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 14 }}>
        <label>
          <span style={labelStyle}>Email</span>
          <input className="input-field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          <span style={labelStyle}>Password</span>
          <input className="input-field" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        {error && <p style={{ color: '#f87171', fontSize: 14, margin: 0 }}>{error}</p>}
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p style={{ marginTop: 16, fontSize: 14, color: '#9ca3af' }}>
        New here? <Link to="/register" style={{ color: '#a78bfa' }}>Create account</Link>
      </p>
    </AuthShell>
  )
}

const labelStyle: React.CSSProperties = { display: 'block', marginBottom: 6, fontSize: 13, color: '#9ca3af' }

function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div className="glass" style={{ width: '100%', maxWidth: 420, padding: 32, borderRadius: 20 }}>
        <h1 className="gradient-text" style={{ margin: '0 0 6px', fontSize: 28 }}>{title}</h1>
        <p style={{ margin: '0 0 24px', color: '#9ca3af', fontSize: 14 }}>{subtitle}</p>
        {children}
      </div>
    </div>
  )
}

export { AuthShell }
