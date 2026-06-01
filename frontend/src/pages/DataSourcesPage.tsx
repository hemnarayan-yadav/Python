import { useEffect, useState } from 'react'
import { dataApi, type DataSource } from '../api/client'

export default function DataSourcesPage() {
  const [sources, setSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)

  // Form state
  const [form, setForm] = useState({
    name: '',
    description: '',
    api_url: '',
    auth_type: 'none' as string,
    auth_value: '',
    auth_header: '',
    http_method: 'GET' as string,
    data_path: '',
    refresh_interval: 300,
    custom_headers: '' as string, // JSON string for extra headers
  })

  const loadSources = async () => {
    setLoading(true)
    try {
      const data = await dataApi.getSources()
      setSources(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadSources() }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      let request_headers: Record<string, string> | undefined
      if (form.custom_headers.trim()) {
        try {
          request_headers = JSON.parse(form.custom_headers)
        } catch {
          setError('Custom Headers must be valid JSON')
          return
        }
      }
      const { custom_headers: _, ...rest } = form
      await dataApi.createSource({
        ...rest,
        refresh_interval: Number(form.refresh_interval),
        auth_value: form.auth_value || undefined,
        auth_header: form.auth_header || undefined,
        data_path: form.data_path || undefined,
        description: form.description || undefined,
        request_headers,
      })
      setShowForm(false)
      setForm({ name: '', description: '', api_url: '', auth_type: 'none', auth_value: '', auth_header: '', http_method: 'GET', data_path: '', refresh_interval: 300, custom_headers: '' })
      loadSources()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create')
    }
  }

  const handleRefresh = async (id: number) => {
    try {
      await dataApi.refreshSource(id)
      loadSources()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refresh failed')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return
    try {
      await dataApi.deleteSource(id)
      loadSources()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="gradient-text" style={{ margin: '0 0 8px', fontSize: 26 }}>Data Sources</h1>
          <p style={{ margin: 0, color: '#9ca3af', fontSize: 14 }}>
            Organization ke multiple APIs add karein — har source ka data alag table me dikhega.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add Source'}
        </button>
      </div>

      {error && (
        <div className="glass" style={{ padding: 14, borderRadius: 12, color: '#f87171' }}>{error}</div>
      )}

      {showForm && (
        <form className="glass" style={{ padding: 24, borderRadius: 16, display: 'grid', gap: 16 }} onSubmit={handleSubmit}>
          <h3 style={{ margin: 0, color: '#c4b5fd' }}>New Data Source</h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Name *</label>
              <input className="input-field" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div>
              <label style={labelStyle}>API URL *</label>
              <input className="input-field" value={form.api_url} onChange={e => setForm({ ...form, api_url: e.target.value })} required />
            </div>
          </div>

          <div>
            <label style={labelStyle}>Description</label>
            <input className="input-field" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Auth Type</label>
              <select className="input-field" value={form.auth_type} onChange={e => setForm({ ...form, auth_type: e.target.value })}>
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
                <option value="header">Custom Header</option>
                <option value="none">No Auth</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Auth Value</label>
              <input className="input-field" type="password" value={form.auth_value} onChange={e => setForm({ ...form, auth_value: e.target.value })} placeholder="Token / API Key" />
            </div>
            <div>
              <label style={labelStyle}>Auth Header</label>
              <input className="input-field" value={form.auth_header} onChange={e => setForm({ ...form, auth_header: e.target.value })} placeholder="e.g. X-API-Key" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>HTTP Method</label>
              <select className="input-field" value={form.http_method} onChange={e => setForm({ ...form, http_method: e.target.value })}>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
              </select>
            </div>
            <div>
              <label style={labelStyle}>Data Path (nested data location)</label>
              <input className="input-field" value={form.data_path} onChange={e => setForm({ ...form, data_path: e.target.value })} placeholder="e.g. data.prospects" />
            </div>
            <div>
              <label style={labelStyle}>Refresh (seconds)</label>
              <input className="input-field" type="number" value={form.refresh_interval} onChange={e => setForm({ ...form, refresh_interval: Number(e.target.value) })} min={60} max={86400} />
            </div>
          </div>

          <div>
            <label style={labelStyle}>Custom Headers (JSON) — for APIs needing multiple auth headers</label>
            <textarea
              className="input-field"
              rows={3}
              value={form.custom_headers}
              onChange={e => setForm({ ...form, custom_headers: e.target.value })}
              placeholder={'{"token": "your-jwt-token", "x-api-key": "your-key", "college_id": "386"}'}
              style={{ fontFamily: 'monospace', fontSize: 12 }}
            />
          </div>

          <button type="submit" className="btn-primary" style={{ justifySelf: 'start' }}>Create Source</button>
        </form>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', color: '#6b7280', padding: 40 }}>Loading sources...</div>
      ) : sources.length === 0 ? (
        <div className="glass" style={{ padding: 40, borderRadius: 16, textAlign: 'center', color: '#6b7280' }}>
          No data sources yet. Click "+ Add Source" to connect your first API.
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          {sources.map(src => (
            <div key={src.id} className="glass" style={{ padding: 20, borderRadius: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 style={{ margin: '0 0 6px', color: '#e5e7eb' }}>
                    {src.name}
                    <span style={{
                      fontSize: 11, marginLeft: 10, padding: '2px 8px', borderRadius: 10,
                      background: src.is_active ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
                      color: src.is_active ? '#34d399' : '#f87171',
                    }}>
                      {src.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </h3>
                  {src.description && <p style={{ margin: '0 0 8px', color: '#9ca3af', fontSize: 13 }}>{src.description}</p>}
                  <div style={{ fontSize: 12, color: '#6b7280', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    <span>URL: <code style={{ color: '#a78bfa' }}>{src.api_url}</code></span>
                    <span>Method: {src.http_method}</span>
                    <span>Auth: {src.auth_type} {src.has_auth ? '✓' : '✗'}</span>
                    {src.data_path && <span>Path: {src.data_path}</span>}
                    <span>Refresh: {src.refresh_interval}s</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="button" className="btn-ghost" style={{ fontSize: 12 }} onClick={() => handleRefresh(src.id)}>
                    Refresh Now
                  </button>
                  <button type="button" className="btn-ghost" style={{ fontSize: 12, color: '#f87171' }} onClick={() => handleDelete(src.id)}>
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 4 }
