import { useEffect, useState } from 'react'
import { dataApi, type DataSource, type AnalyticsResult } from '../api/client'

export default function AnalyticsPage() {
  const [sources, setSources] = useState<DataSource[]>([])
  const [selectedSource, setSelectedSource] = useState<number | null>(null)
  const [groupBy, setGroupBy] = useState('')
  const [aggregate, setAggregate] = useState('count')
  const [aggregateField, setAggregateField] = useState('')
  const [result, setResult] = useState<AnalyticsResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [fields, setFields] = useState<string[]>([])

  useEffect(() => {
    dataApi.getSources().then(data => {
      setSources(data)
      if (data.length > 0) setSelectedSource(data[0].id)
    })
  }, [])

  useEffect(() => {
    if (!selectedSource) return
    dataApi.getFieldConfigs(selectedSource).then(configs => {
      setFields(configs.map(c => c.field_key))
    }).catch(() => {})
  }, [selectedSource])

  const runAnalysis = async () => {
    if (!selectedSource) return
    setLoading(true)
    setError('')
    try {
      const data = await dataApi.runAnalytics({
        source_id: selectedSource,
        group_by: groupBy || undefined,
        aggregate: aggregate || 'count',
        aggregate_field: aggregateField || undefined,
      })
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const maxVal = result ? Math.max(...result.result.map(r => Number(r._value) || 0), 1) : 1

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      <div>
        <h1 className="gradient-text" style={{ margin: '0 0 8px', fontSize: 26 }}>Analytics</h1>
        <p style={{ margin: 0, color: '#9ca3af', fontSize: 14 }}>
          Organization data ka analysis — group by, aggregate, aur visualize karein.
        </p>
      </div>

      <div className="glass" style={{ padding: 20, borderRadius: 16, display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-end' }}>
        <div>
          <label style={labelStyle}>Data Source</label>
          <select className="input-field" value={selectedSource ?? ''} onChange={e => setSelectedSource(Number(e.target.value))}>
            {sources.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Group By</label>
          <select className="input-field" value={groupBy} onChange={e => setGroupBy(e.target.value)}>
            <option value="">— None (whole dataset) —</option>
            {fields.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>
        <div>
          <label style={labelStyle}>Aggregate</label>
          <select className="input-field" value={aggregate} onChange={e => setAggregate(e.target.value)}>
            <option value="count">Count</option>
            <option value="sum">Sum</option>
            <option value="avg">Average</option>
            <option value="min">Min</option>
            <option value="max">Max</option>
          </select>
        </div>
        {aggregate !== 'count' && (
          <div>
            <label style={labelStyle}>Aggregate Field</label>
            <select className="input-field" value={aggregateField} onChange={e => setAggregateField(e.target.value)}>
              <option value="">— select —</option>
              {fields.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
        )}
        <button type="button" className="btn-primary" onClick={runAnalysis} disabled={loading}>
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {error && (
        <div className="glass" style={{ padding: 14, borderRadius: 12, color: '#f87171' }}>{error}</div>
      )}

      {result && (
        <>
          {/* Summary */}
          <div className="glass" style={{ padding: 20, borderRadius: 16 }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 16, color: '#c4b5fd' }}>Summary — {result.source_name}</h3>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
              {Object.entries(result.summary).slice(0, 12).map(([k, v]) => (
                <div key={k} style={{ fontSize: 13 }}>
                  <span style={{ color: '#6b7280' }}>{k}: </span>
                  <span style={{ color: '#e5e7eb', fontWeight: 600 }}>{String(v)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bar Chart */}
          <div className="glass" style={{ padding: 20, borderRadius: 16 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 16, color: '#c4b5fd' }}>
              {aggregate.toUpperCase()}{aggregateField ? ` of ${aggregateField}` : ''} {groupBy ? `by ${groupBy}` : ''}
            </h3>
            <div style={{ display: 'grid', gap: 8 }}>
              {result.result.map((row, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 140, fontSize: 13, color: '#9ca3af', textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {row._group}
                  </div>
                  <div style={{ flex: 1, height: 24, borderRadius: 6, background: 'rgba(255,255,255,0.04)' }}>
                    <div style={{
                      width: `${Math.max((Number(row._value) / maxVal) * 100, 2)}%`,
                      height: '100%',
                      borderRadius: 6,
                      background: 'linear-gradient(90deg, #7c3aed, #a78bfa)',
                      display: 'flex',
                      alignItems: 'center',
                      paddingLeft: 8,
                      fontSize: 11,
                      color: '#fff',
                      fontWeight: 600,
                    }}>
                      {row._value}
                    </div>
                  </div>
                  <div style={{ width: 50, fontSize: 12, color: '#6b7280', textAlign: 'right' }}>
                    n={row._count}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Table */}
          <div className="glass" style={{ padding: 20, borderRadius: 16, overflowX: 'auto' }}>
            <h3 style={{ margin: '0 0 12px', fontSize: 16, color: '#c4b5fd' }}>Raw Results</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={thStyle}>Group</th>
                  <th style={thStyle}>Value</th>
                  <th style={thStyle}>Count</th>
                </tr>
              </thead>
              <tbody>
                {result.result.map((row, i) => (
                  <tr key={i}>
                    <td style={tdStyle}>{row._group}</td>
                    <td style={{ ...tdStyle, textAlign: 'right', fontWeight: 600, color: '#a78bfa' }}>{row._value}</td>
                    <td style={{ ...tdStyle, textAlign: 'right' }}>{row._count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

const labelStyle: React.CSSProperties = { display: 'block', fontSize: 12, color: '#9ca3af', marginBottom: 4 }
const thStyle: React.CSSProperties = { textAlign: 'left', padding: '8px 12px', borderBottom: '1px solid rgba(255,255,255,0.08)', color: '#6b7280', fontWeight: 600 }
const tdStyle: React.CSSProperties = { padding: '8px 12px', borderBottom: '1px solid rgba(255,255,255,0.04)', color: '#e5e7eb' }
