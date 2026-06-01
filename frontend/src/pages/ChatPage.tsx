import { useEffect, useRef, useState } from 'react'
import { marked } from 'marked'
import { api } from '../api/client'
import { useOrgRecords } from '../context/OrgRecordsContext'

type Msg = { role: string; content: string }

export default function ChatPage() {
  const { records } = useOrgRecords()
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send(e: React.FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setLoading(true)
    try {
      const data = await api<{ reply: string }>('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ message: text }),
      })
      setMessages((m) => [...m, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: `⚠️ ${err instanceof Error ? err.message : 'Error'}` }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      <h1 className="gradient-text" style={{ marginTop: 0 }}>AI Chat</h1>
      {records && (
        <p style={{ color: '#9ca3af', fontSize: 13, margin: '0 0 12px' }}>
          Context: {records.total} org users · {records.columns.length} dynamic fields from API
        </p>
      )}
      <div className="glass" style={{ flex: 1, borderRadius: 16, padding: 16, overflowY: 'auto', marginBottom: 12 }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              marginBottom: 12,
              padding: 12,
              borderRadius: 12,
              background: m.role === 'user' ? 'rgba(124,58,237,0.15)' : 'rgba(255,255,255,0.03)',
              marginLeft: m.role === 'user' ? 'auto' : 0,
              maxWidth: '85%',
            }}
          >
            <div
              className="markdown-content"
              dangerouslySetInnerHTML={{ __html: marked.parse(m.content) }}
            />
          </div>
        ))}
        {loading && <p style={{ color: '#9ca3af' }}>Thinking...</p>}
        <div ref={endRef} />
      </div>
      <form onSubmit={send} style={{ display: 'flex', gap: 8 }}>
        <input className="input-field" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about your users..." />
        <button className="btn-primary" type="submit" disabled={loading}>Send</button>
      </form>
    </div>
  )
}
