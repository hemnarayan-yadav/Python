import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function OnboardingPage() {
  const { user, completeOnboarding } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    industry: '',
    api_url: '',
    api_key: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (!user) return <Navigate to="/login" replace />
  if (user.onboarding_completed) return <Navigate to="/dashboard" replace />

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await completeOnboarding({
        name: form.name,
        industry: form.industry || undefined,
        api_url: form.api_url || undefined,
        api_key: form.api_key || undefined,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Setup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <div className="glass" style={{ width: '100%', maxWidth: 520, padding: 32, borderRadius: 20 }}>
        <p style={{ color: '#a78bfa', fontSize: 13, margin: '0 0 8px' }}>Step 2 of 2</p>
        <h1 className="gradient-text" style={{ margin: '0 0 8px' }}>Organization Setup</h1>
        <p style={{ color: '#9ca3af', fontSize: 14, marginBottom: 24 }}>
          Signup tab tak complete nahi hoga jab tak organization details fill na ho.
          Dashboard tab tak band rahega.
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: 14 }}>
          <label>
            <span style={label}>Organization Name *</span>
            <input className="input-field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </label>
          <label>
            <span style={label}>Industry</span>
            <input className="input-field" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} placeholder="e.g. SaaS, Retail" />
          </label>
          <label>
            <span style={label}>Users API URL</span>
            <input
              className="input-field"
              value={form.api_url}
              onChange={(e) => setForm({ ...form, api_url: e.target.value })}
              placeholder="https://your-api.com/users"
            />
            <small style={{ color: '#6b7280' }}>Khali chhodo to demo data dikhega. API JSON array ya data/users key return kare.</small>
          </label>
          <label>
            <span style={label}>API Key (optional)</span>
            <input className="input-field" type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
          </label>
          {error && <p style={{ color: '#f87171', margin: 0, fontSize: 14 }}>{error}</p>}
          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? 'Saving...' : 'Complete Setup & Open Dashboard'}
          </button>
        </form>
      </div>
    </div>
  )
}

const label: React.CSSProperties = { display: 'block', marginBottom: 6, fontSize: 13, color: '#9ca3af' }
