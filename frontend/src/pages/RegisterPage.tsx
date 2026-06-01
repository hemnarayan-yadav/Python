import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { AuthShell } from './LoginPage'

export default function RegisterPage() {
  const { register, user } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', age: 25 })
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
      await register(form)
      navigate('/onboarding')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Create account" subtitle="Step 1 — Sign up (organization setup next)">
      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 14 }}>
        {(['name', 'email', 'password'] as const).map((field) => (
          <label key={field}>
            <span style={{ display: 'block', marginBottom: 6, fontSize: 13, color: '#9ca3af', textTransform: 'capitalize' }}>
              {field}
            </span>
            <input
              className="input-field"
              type={field === 'password' ? 'password' : field === 'email' ? 'email' : 'text'}
              value={form[field]}
              onChange={(e) => setForm({ ...form, [field]: e.target.value })}
              required
            />
          </label>
        ))}
        <label>
          <span style={{ display: 'block', marginBottom: 6, fontSize: 13, color: '#9ca3af' }}>Age</span>
          <input
            className="input-field"
            type="number"
            min={1}
            max={99}
            value={form.age}
            onChange={(e) => setForm({ ...form, age: Number(e.target.value) })}
            required
          />
        </label>
        {error && <p style={{ color: '#f87171', fontSize: 14, margin: 0 }}>{error}</p>}
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Creating...' : 'Sign up'}
        </button>
      </form>
      <p style={{ marginTop: 16, fontSize: 14, color: '#9ca3af' }}>
        Already have an account? <Link to="/login" style={{ color: '#a78bfa' }}>Login</Link>
      </p>
    </AuthShell>
  )
}
