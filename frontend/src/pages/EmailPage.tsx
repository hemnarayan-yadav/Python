import { useEffect, useState } from 'react'
import { dataApi, type DataSource, type EmailTemplate } from '../api/client'

export default function EmailPage() {
  const [sources, setSources] = useState<DataSource[]>([])
  const [templates, setTemplates] = useState<EmailTemplate[]>([])
  const [selectedSource, setSelectedSource] = useState<number | null>(null)
  const [fields, setFields] = useState<{ field_key: string; is_email_field: boolean; is_name_field: boolean }[]>([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  // Template form
  const [showTemplateForm, setShowTemplateForm] = useState(false)
  const [templateForm, setTemplateForm] = useState({ name: '', subject: '', body_html: '' })

  // Send form
  const [showSendForm, setShowSendForm] = useState(false)
  const [sendForm, setSendForm] = useState({
    template_id: '' as string,
    subject: '',
    body_html: '',
    email_field: '',
    name_field: '',
  })
  const [sending, setSending] = useState(false)
  const [sendResult, setSendResult] = useState<{ queued: number; failed: number } | null>(null)

  useEffect(() => {
    dataApi.getSources().then(data => {
      setSources(data)
      if (data.length > 0) setSelectedSource(data[0].id)
    })
    dataApi.getEmailTemplates().then(setTemplates).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedSource) return
    dataApi.getFieldConfigs(selectedSource).then(configs => {
      setFields(configs.map(c => ({
        field_key: c.field_key,
        is_email_field: c.is_email_field,
        is_name_field: c.is_name_field,
      })))
      // Auto-detect email and name fields
      const emailF = configs.find(c => c.is_email_field)
      const nameF = configs.find(c => c.is_name_field)
      setSendForm(prev => ({
        ...prev,
        email_field: emailF?.field_key || prev.email_field,
        name_field: nameF?.field_key || prev.name_field,
      }))
    }).catch(() => {})
  }, [selectedSource])

  const handleCreateTemplate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await dataApi.createEmailTemplate(templateForm)
      setTemplateForm({ name: '', subject: '', body_html: '' })
      setShowTemplateForm(false)
      const updated = await dataApi.getEmailTemplates()
      setTemplates(updated)
      setSuccess('Template created!')
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed')
    }
  }

  const handleDeleteTemplate = async (id: number) => {
    if (!confirm('Delete this template?')) return
    try {
      await dataApi.deleteEmailTemplate(id)
      setTemplates(prev => prev.filter(t => t.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed')
    }
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedSource) return
    setSending(true)
    setError('')
    setSendResult(null)
    try {
      const payload: Record<string, unknown> = {
        source_id: selectedSource,
        email_field: sendForm.email_field || undefined,
        name_field: sendForm.name_field || undefined,
      }
      if (sendForm.template_id) {
        payload.template_id = Number(sendForm.template_id)
      } else {
        payload.subject = sendForm.subject
        payload.body_html = sendForm.body_html
      }
      const result = await dataApi.sendEmails(payload)
      setSendResult({ queued: result.queued, failed: result.failed })
      setSuccess(`Emails sent! ${result.queued} delivered, ${result.failed} failed.`)
      setTimeout(() => setSuccess(''), 5000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Send failed')
    } finally {
      setSending(false)
    }
  }

  const selectedTemplate = sendForm.template_id ? templates.find(t => t.id === Number(sendForm.template_id)) : null

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <div>
        <h1 className="gradient-text" style={{ margin: '0 0 8px', fontSize: 26 }}>Email Center</h1>
        <p style={{ margin: 0, color: '#9ca3af', fontSize: 14 }}>
          Organization data ke users ko bulk emails bhejein — templates create karein aur {"{{field_key}}"} placeholders use karein.
        </p>
      </div>

      {error && <div className="glass" style={{ padding: 14, borderRadius: 12, color: '#f87171' }}>{error}</div>}
      {success && <div className="glass" style={{ padding: 14, borderRadius: 12, color: '#34d399' }}>{success}</div>}

      {/* ── Email Templates ── */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 18, color: '#e5e7eb' }}>Email Templates</h2>
          <button type="button" className="btn-primary" onClick={() => setShowTemplateForm(!showTemplateForm)}>
            {showTemplateForm ? 'Cancel' : '+ New Template'}
          </button>
        </div>

        {showTemplateForm && (
          <form className="glass" style={{ padding: 20, borderRadius: 16, display: 'grid', gap: 14, marginBottom: 16 }} onSubmit={handleCreateTemplate}>
            <div>
              <label style={labelStyle}>Template Name *</label>
              <input className="input-field" value={templateForm.name} onChange={e => setTemplateForm({ ...templateForm, name: e.target.value })} required />
            </div>
            <div>
              <label style={labelStyle}>Subject * (use {'{{field_key}}'} for dynamic values)</label>
              <input className="input-field" value={templateForm.subject} onChange={e => setTemplateForm({ ...templateForm, subject: e.target.value })} required />
            </div>
            <div>
              <label style={labelStyle}>Body HTML * (use {'{{field_key}}'} for personalization)</label>
              <textarea
                className="input-field"
                rows={6}
                value={templateForm.body_html}
                onChange={e => setTemplateForm({ ...templateForm, body_html: e.target.value })}
                required
                placeholder={'<h1>Hi {{name}},</h1>\n<p>Your account status: {{status}}</p>'}
              />
            </div>
            {fields.length > 0 && (
              <div style={{ fontSize: 12, color: '#6b7280' }}>
                Available fields: {fields.map(f => f.field_key).join(', ')}
              </div>
            )}
            <button type="submit" className="btn-primary" style={{ justifySelf: 'start' }}>Save Template</button>
          </form>
        )}

        {templates.length === 0 ? (
          <div className="glass" style={{ padding: 24, borderRadius: 16, textAlign: 'center', color: '#6b7280' }}>
            No templates yet. Create one to start sending personalized emails.
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {templates.map(t => (
              <div key={t.id} className="glass" style={{ padding: 16, borderRadius: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <strong style={{ color: '#e5e7eb' }}>{t.name}</strong>
                    <div style={{ fontSize: 13, color: '#9ca3af', marginTop: 4 }}>Subject: {t.subject}</div>
                    {t.placeholders && t.placeholders.length > 0 && (
                      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>
                        Placeholders: {t.placeholders.map(p => `{{${p}}}`).join(', ')}
                      </div>
                    )}
                  </div>
                  <button type="button" className="btn-ghost" style={{ fontSize: 12, color: '#f87171' }} onClick={() => handleDeleteTemplate(t.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ── Send Emails ── */}
      <section className="glass" style={{ padding: 24, borderRadius: 16 }}>
        <h2 style={{ margin: '0 0 16px', fontSize: 18, color: '#e5e7eb' }}>Send Bulk Email</h2>

        <form style={{ display: 'grid', gap: 14 }} onSubmit={handleSend}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div>
              <label style={labelStyle}>Data Source *</label>
              <select className="input-field" value={selectedSource ?? ''} onChange={e => setSelectedSource(Number(e.target.value))}>
                {sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Email Field *</label>
              <select className="input-field" value={sendForm.email_field} onChange={e => setSendForm({ ...sendForm, email_field: e.target.value })}>
                <option value="">— auto-detect —</option>
                {fields.map(f => <option key={f.field_key} value={f.field_key}>{f.field_key} {f.is_email_field ? '(detected)' : ''}</option>)}
              </select>
            </div>
            <div>
              <label style={labelStyle}>Name Field</label>
              <select className="input-field" value={sendForm.name_field} onChange={e => setSendForm({ ...sendForm, name_field: e.target.value })}>
                <option value="">— auto-detect —</option>
                {fields.map(f => <option key={f.field_key} value={f.field_key}>{f.field_key} {f.is_name_field ? '(detected)' : ''}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label style={labelStyle}>Use Template (or write inline below)</label>
            <select className="input-field" value={sendForm.template_id} onChange={e => setSendForm({ ...sendForm, template_id: e.target.value })}>
              <option value="">— No template (inline) —</option>
              {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>

          {selectedTemplate && (
            <div style={{ fontSize: 12, color: '#9ca3af', padding: 12, borderRadius: 10, background: 'rgba(124,58,237,0.08)' }}>
              <div>Subject: <strong>{selectedTemplate.subject}</strong></div>
              <div style={{ marginTop: 4, maxHeight: 80, overflow: 'auto' }}>{selectedTemplate.body_html.substring(0, 200)}...</div>
            </div>
          )}

          {!sendForm.template_id && (
            <>
              <div>
                <label style={labelStyle}>Subject *</label>
                <input className="input-field" value={sendForm.subject} onChange={e => setSendForm({ ...sendForm, subject: e.target.value })} />
              </div>
              <div>
                <label style={labelStyle}>Body HTML *</label>
                <textarea className="input-field" rows={4} value={sendForm.body_html} onChange={e => setSendForm({ ...sendForm, body_html: e.target.value })} />
              </div>
            </>
          )}

          <button type="submit" className="btn-primary" disabled={sending} style={{ justifySelf: 'start' }}>
            {sending ? 'Sending...' : 'Send to All Records'}
          </button>
        </form>

        {sendResult && (
          <div style={{ marginTop: 16, fontSize: 14, color: '#34d399' }}>
            ✓ Sent: {sendResult.queued} | Failed: {sendResult.failed}
          </div>
        )}
      </section>
    </div>
  )
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 4 }
