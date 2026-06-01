import type { ColumnSchema } from '../api/client'

type Props = {
  columns: string[]
  schema?: ColumnSchema[]
  rows: Record<string, unknown>[]
  loading?: boolean
  emptyMessage?: string
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

function labelize(key: string, schema?: ColumnSchema[]): string {
  return schema?.find((s) => s.key === key)?.label ?? key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function cellAlign(type?: string): 'left' | 'right' {
  return type === 'number' ? 'right' : 'left'
}

export default function DynamicTable({
  columns,
  schema,
  rows,
  loading,
  emptyMessage = 'No records returned from organization API.',
}: Props) {
  if (loading) {
    return (
      <div className="glass" style={{ padding: 32, borderRadius: 16, textAlign: 'center', color: '#9ca3af' }}>
        Organization API se data load ho raha hai...
      </div>
    )
  }

  if (!columns.length) {
    return (
      <div className="glass" style={{ padding: 24, borderRadius: 16, color: '#9ca3af' }}>
        API response me koi column nahi mila. JSON array of objects bhejein.
      </div>
    )
  }

  const schemaMap = new Map(schema?.map((s) => [s.key, s]) ?? [])

  return (
    <div className="glass" style={{ borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ overflowX: 'auto', maxHeight: 'calc(100vh - 280px)' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: Math.max(640, columns.length * 120) }}>
          <thead style={{ position: 'sticky', top: 0, background: 'rgba(15,15,20,0.95)', zIndex: 1 }}>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
              {columns.map((col) => {
                const meta = schemaMap.get(col)
                return (
                  <th
                    key={col}
                    style={{
                      textAlign: cellAlign(meta?.type),
                      padding: '12px 14px',
                      fontSize: 11,
                      color: '#9ca3af',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                      whiteSpace: 'nowrap',
                      fontWeight: 600,
                    }}
                    title={meta ? `Type: ${meta.type}` : col}
                  >
                    {labelize(col, schema)}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, idx) => (
              <tr
                key={idx}
                style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.02)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                {columns.map((col) => {
                  const meta = schemaMap.get(col)
                  return (
                    <td
                      key={col}
                      style={{
                        padding: '11px 14px',
                        fontSize: 13,
                        color: '#e5e7eb',
                        textAlign: cellAlign(meta?.type),
                        maxWidth: 260,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontVariantNumeric: meta?.type === 'number' ? 'tabular-nums' : undefined,
                      }}
                      title={formatCell(row[col])}
                    >
                      {formatCell(row[col])}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && (
        <div style={{ padding: 24, color: '#9ca3af', textAlign: 'center' }}>{emptyMessage}</div>
      )}
    </div>
  )
}

export function exportCsv(columns: string[], rows: Record<string, unknown>[], filename = 'org-records.csv') {
  const escape = (v: unknown) => {
    const s = v == null ? '' : String(v)
    return `"${s.replace(/"/g, '""')}"`
  }
  const header = columns.map(escape).join(',')
  const body = rows.map((row) => columns.map((c) => escape(row[c])).join(',')).join('\n')
  const blob = new Blob([`${header}\n${body}`], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
