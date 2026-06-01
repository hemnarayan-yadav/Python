import { useEffect, useState } from 'react'
import { marked } from 'marked'
import { api, dataApi, type MultiSourceSummary } from '../api/client'
import { useOrgRecords } from '../context/OrgRecordsContext'
import DynamicTable from '../components/DynamicTable'

// Ensure marked.parse returns string synchronously
function parseMarkdown(md: string): string {
  const result = marked.parse(md)
  return typeof result === 'string' ? result : ''
}

export default function DashboardPage() {
  const { records, loading, filteredRows, visibleColumns } = useOrgRecords()
  const [insight, setInsight] = useState('')
  const [insightLoading, setInsightLoading] = useState(false)
  const [provider, setProvider] = useState('')
  const [sourcesSummary, setSourcesSummary] = useState<MultiSourceSummary | null>(null)

  useEffect(() => {
    fetch('/ai/providers')
      .then((r) => r.json())
      .then((d) => setProvider(d.active || ''))
      .catch(() => setProvider(''))

    dataApi.getSourcesSummary().then(setSourcesSummary).catch(() => {})
  }, [])

  async function fetchInsights() {
    setInsightLoading(true)
    try {
      const data = await api<{ insight: string }>('/ai/insights', {
        method: 'POST',
        body: JSON.stringify({}),
      })
      setInsight(data.insight)
    } catch (e) {
      setInsight(e instanceof Error ? e.message : 'Failed')
    } finally {
      setInsightLoading(false)
    }
  }

  const previewCols = visibleColumns.slice(0, 10)
  const emailCol = records?.columns.find((c) => c === 'email' || c.includes('email'))

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <h1 className="gradient-text" style={{ margin: 0, fontSize: 28 }}>Dashboard</h1>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))', gap: 16 }}>
        <Stat label="Data Sources" value={String(sourcesSummary?.total_sources ?? 0)} color="#818cf8" />
        <Stat label="Total Records" value={String(sourcesSummary?.total_records ?? records?.total ?? 0)} color="#fbbf24" />
        <Stat label="Dynamic Columns" value={String(records?.columns.length ?? 0)} color="#a78bfa" />
        <Stat label="Data Source" value={records?.source ?? '—'} color="#34d399" />
        <Stat label="AI Provider" value={provider || '—'} />
      </div>

      {sourcesSummary && sourcesSummary.sources.length > 0 && (
        <section className="glass" style={{ padding: 20, borderRadius: 16 }}>
          <h2 style={{ margin: '0 0 12px', fontSize: 18 }}>Connected Data Sources</h2>
          <div style={{ display: 'grid', gap: 8 }}>
            {sourcesSummary.sources.map(src => (
              <div key={src.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderRadius: 10, background: 'rgba(255,255,255,0.03)' }}>
                <div>
                  <span style={{ color: '#e5e7eb', fontWeight: 600 }}>{src.name}</span>
                  <span style={{ fontSize: 12, color: '#6b7280', marginLeft: 12 }}>{src.columns} columns · {src.row_count} rows</span>
                </div>
                <span style={{
                  fontSize: 11, padding: '2px 8px', borderRadius: 10,
                  background: src.is_active ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
                  color: src.is_active ? '#34d399' : '#f87171',
                }}>
                  {src.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {records && emailCol && (
        <p style={{ margin: 0, fontSize: 13, color: '#9ca3af' }}>
          Mail campaigns ke liye <code style={{ color: '#c4b5fd' }}>{emailCol}</code> column detect hui (
          {records.schema.find((s) => s.key === emailCol)?.type ?? 'string'}).
        </p>
      )}

      <section className="glass" style={{ padding: 20, borderRadius: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
          <h2 style={{ margin: 0, fontSize: 18 }}>AI Insights (org data + CRUD users)</h2>
          <button type="button" className="btn-primary" onClick={fetchInsights} disabled={insightLoading}>
            {insightLoading ? 'Generating...' : 'Generate Insights'}
          </button>
        </div>
        <div
          className="markdown-content"
          dangerouslySetInnerHTML={{
            __html: parseMarkdown(insight || 'Generate Insights se organization users par analysis.'),
          }}
        />
      </section>

      <section>
        <h2 style={{ fontSize: 18, marginBottom: 12 }}>
          Organization API Preview ({previewCols.length} of {records?.columns.length ?? 0} columns)
        </h2>
        <DynamicTable
          columns={previewCols}
          schema={records?.schema}
          rows={filteredRows.slice(0, 8)}
          loading={loading && !records}
        />
      </section>
    </div>
  )
}

function Stat({ label, value, color = '#e5e7eb' }: { label: string; value: string; color?: string }) {
  return (
    <div className="glass" style={{ padding: 20, borderRadius: 16 }}>
      <div style={{ fontSize: 12, color: '#6b7280', textTransform: 'uppercase', marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    </div>
  )
}
