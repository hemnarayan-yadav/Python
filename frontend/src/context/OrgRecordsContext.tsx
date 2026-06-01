import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, type OrgRecords } from '../api/client'

type OrgRecordsContextValue = {
  records: OrgRecords | null
  loading: boolean
  error: string
  refresh: () => Promise<void>
  /** Filtered view for UI (search applied client-side; server pagination later) */
  filteredRows: Record<string, unknown>[]
  search: string
  setSearch: (q: string) => void
  visibleColumns: string[]
  toggleColumn: (key: string) => void
  showAllColumns: () => void
}

const OrgRecordsContext = createContext<OrgRecordsContextValue | null>(null)

export function OrgRecordsProvider({ children }: { children: ReactNode }) {
  const [records, setRecords] = useState<OrgRecords | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [hiddenColumns, setHiddenColumns] = useState<Set<string>>(new Set())

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api<OrgRecords>('/organization/records')
      setRecords(data)
      setHiddenColumns(new Set())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load organization data')
      setRecords(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const visibleColumns = useMemo(() => {
    if (!records) return []
    return records.columns.filter((c) => !hiddenColumns.has(c))
  }, [records, hiddenColumns])

  const filteredRows = useMemo(() => {
    if (!records) return []
    const q = search.trim().toLowerCase()
    if (!q) return records.rows
    return records.rows.filter((row) =>
      records.columns.some((col) => {
        const v = row[col]
        if (v == null) return false
        return String(v).toLowerCase().includes(q)
      }),
    )
  }, [records, search])

  const toggleColumn = useCallback((key: string) => {
    setHiddenColumns((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }, [])

  const showAllColumns = useCallback(() => setHiddenColumns(new Set()), [])

  const value = useMemo(
    () => ({
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
    }),
    [
      records,
      loading,
      error,
      refresh,
      filteredRows,
      search,
      visibleColumns,
      toggleColumn,
      showAllColumns,
    ],
  )

  return (
    <OrgRecordsContext.Provider value={value}>{children}</OrgRecordsContext.Provider>
  )
}

export function useOrgRecords() {
  const ctx = useContext(OrgRecordsContext)
  if (!ctx) throw new Error('useOrgRecords must be used within OrgRecordsProvider')
  return ctx
}

/** For AI / mail modules — export raw dataset without UI state */
export function useOrgRecordsData() {
  const { records } = useOrgRecords()
  return records
}
