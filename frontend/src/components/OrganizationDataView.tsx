import { useEffect } from 'react'
import { useAuth } from '../context/AuthContext'
import { useOrgRecords } from '../context/OrgRecordsContext'
import DynamicTable, { exportCsv } from './DynamicTable'

export default function OrganizationDataView() {
  const { user } = useAuth()
  const {
    records,
    loading,
    error,
    refresh,
    filteredRows,
    search,
    setSearch,
    visibleColumns,
    toggleColumn,
    showAllColumns,
  } = useOrgRecords()

  useEffect(() => {
    if (!records && !loading) refresh()
  }, [records, loading, refresh])

  const orgName = user?.organization?.name ?? 'Organization'
  const apiConfigured = Boolean(user?.organization?.api_url)

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1 className="gradient-text" style={{ margin: '0 0 8px', fontSize: 26 }}>
          Organization Users
        </h1>
        <p style={{ margin: 0, color: '#9ca3af', fontSize: 14, maxWidth: 720, lineHeight: 1.6 }}>
          <strong>{orgName}</strong> ki API se JSON aata hai — table columns automatically banenge.
          Ek org ke 50 keys hon ya doosre ke 20, UI usi ke hisaab se adapt hogi.
          Ye data analysis, AI chat aur mail features ke liye shared source hai.
        </p>
      </div>

      <div
        className="glass"
        style={{
          padding: 16,
          borderRadius: 14,
          marginBottom: 16,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 12,
          alignItems: 'center',
        }}
      >
        <input
          className="input-field"
          style={{ flex: '1 1 220px', maxWidth: 360 }}
          placeholder="Search across all columns..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="button" className="btn-ghost" onClick={() => refresh()} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh API'}
        </button>
        {records && (
          <button
            type="button"
            className="btn-ghost"
            onClick={() => exportCsv(visibleColumns, filteredRows)}
            disabled={!filteredRows.length}
          >
            Export CSV
          </button>
        )}
      </div>

      {records && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 14, alignItems: 'center' }}>
          <span style={{ fontSize: 12, color: '#6b7280' }}>
            {records.columns.length} columns · {filteredRows.length}/{records.total} rows · source:{' '}
            <strong style={{ color: apiConfigured ? '#34d399' : '#fbbf24' }}>{records.source}</strong>
            {!apiConfigured && ' (demo — onboarding me API URL add karein)'}
          </span>
          <button type="button" className="btn-ghost" style={{ fontSize: 12, padding: '4px 10px' }} onClick={showAllColumns}>
            Show all columns
          </button>
        </div>
      )}

      {records && records.columns.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
          {records.columns.map((col) => {
            const hidden = !visibleColumns.includes(col)
            const meta = records.schema.find((s) => s.key === col)
            return (
              <button
                key={col}
                type="button"
                onClick={() => toggleColumn(col)}
                style={{
                  fontSize: 11,
                  padding: '4px 10px',
                  borderRadius: 20,
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: hidden ? 'transparent' : 'rgba(124,58,237,0.2)',
                  color: hidden ? '#6b7280' : '#c4b5fd',
                  cursor: 'pointer',
                }}
                title={meta ? `${meta.label} (${meta.type})` : col}
              >
                {meta?.label ?? col}
              </button>
            )
          })}
        </div>
      )}

      {error && (
        <div className="glass" style={{ padding: 16, borderRadius: 12, color: '#f87171', marginBottom: 16 }}>
          {error}
        </div>
      )}

      <DynamicTable
        columns={visibleColumns}
        schema={records?.schema}
        rows={filteredRows}
        loading={loading && !records}
        emptyMessage={
          search
            ? 'Search ke liye koi row match nahi hui.'
            : 'Organization API se koi record nahi aaya.'
        }
      />

      {records?.fetched_at && (
        <p style={{ marginTop: 12, fontSize: 12, color: '#6b7280' }}>
          Last synced: {new Date(records.fetched_at).toLocaleString()}
        </p>
      )}
    </div>
  )
}
