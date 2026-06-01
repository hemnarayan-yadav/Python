import { useState } from 'react'
import { marked } from 'marked'
import { api } from '../api/client'

export default function ContentPage() {
  const [genType, setGenType] = useState('email')
  const [userId, setUserId] = useState('')
  const [instructions, setInstructions] = useState('')
  const [result, setResult] = useState('')
  const [loading, setLoading] = useState(false)

  async function generate(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setResult('')
    try {
      const data = await api<{ result: string }>('/ai/generate', {
        method: 'POST',
        body: JSON.stringify({
          content_type: genType,
          user_id: userId ? Number(userId) : null,
          extra_instructions: instructions || null,
        }),
      })
      setResult(data.result)
    } catch (err) {
      setResult(err instanceof Error ? err.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="gradient-text" style={{ marginTop: 0 }}>Content AI</h1>
      <form onSubmit={generate} className="glass" style={{ padding: 20, borderRadius: 16, display: 'grid', gap: 12, maxWidth: 520, marginBottom: 20 }}>
        <select className="input-field" value={genType} onChange={(e) => setGenType(e.target.value)}>
          <option value="email">Email</option>
          <option value="bio">Bio</option>
          <option value="report">Report</option>
          <option value="social_post">Social Post</option>
        </select>
        <input className="input-field" placeholder="User ID (optional)" value={userId} onChange={(e) => setUserId(e.target.value)} />
        <textarea className="input-field" rows={3} placeholder="Extra instructions" value={instructions} onChange={(e) => setInstructions(e.target.value)} />
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Generating...' : 'Generate'}
        </button>
      </form>
      {result && (
        <div
          className="glass markdown-content"
          style={{ padding: 20, borderRadius: 16 }}
          dangerouslySetInnerHTML={{ __html: marked.parse(result) }}
        />
      )}
    </div>
  )
}
