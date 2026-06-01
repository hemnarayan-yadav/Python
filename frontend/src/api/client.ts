const TOKEN_KEY = 'nexus_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(path, { ...options, headers })
  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    const detail = typeof data.detail === 'string'
      ? data.detail
      : JSON.stringify(data.detail ?? data)
    throw new Error(detail || `Request failed (${res.status})`)
  }
  return data as T
}

export type ColumnSchema = {
  key: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'json' | 'null'
  nullable: boolean
}

/** Single source of truth for organization API data — used by table, AI, mail, etc. */
export type OrgRecords = {
  columns: string[]
  schema: ColumnSchema[]
  rows: Record<string, unknown>[]
  total: number
  source: string
  fetched_at: string
}

/** Enhanced paginated records from the data pipeline */
export type PaginatedRecords = {
  columns: string[]
  schema_info: ColumnSchema[]
  rows: Record<string, unknown>[]
  total: number
  page: number
  page_size: number
  total_pages: number
  source_id: number
  source_name: string
  fetched_at: string
  is_cached: boolean
  cache_expires_at?: string
}

export type DataSource = {
  id: number
  org_id: number
  name: string
  description?: string
  api_url: string
  auth_type: string
  has_auth: boolean
  auth_header?: string
  http_method: string
  request_headers?: Record<string, string>
  data_path?: string
  refresh_interval: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export type FieldConfig = {
  id: number
  source_id: number
  field_key: string
  display_label?: string
  field_type?: string
  is_visible: boolean
  is_searchable: boolean
  is_sortable: boolean
  is_filterable: boolean
  display_order: number
  format_pattern?: string
  is_email_field: boolean
  is_name_field: boolean
  is_phone_field: boolean
}

export type MultiSourceSummary = {
  sources: {
    id: number
    name: string
    description?: string
    api_url: string
    is_active: boolean
    row_count: number
    columns: number
    last_fetched?: string
    refresh_interval: number
  }[]
  total_sources: number
  total_records: number
}

export type EmailTemplate = {
  id: number
  org_id: number
  name: string
  subject: string
  body_html: string
  placeholders?: string[]
  created_at: string
  updated_at: string
}

export type AnalyticsResult = {
  source_id: number
  source_name: string
  result: { _group: string; _value: number; _count: number }[]
  summary: Record<string, unknown>
  generated_at: string
}

export type ActionLog = {
  id: number
  action_type: string
  action_detail?: Record<string, unknown>
  status: string
  result_summary?: string
  created_at: string
}

export type AuthUser = {
  id: number
  name: string
  email: string
  age: number
  onboarding_completed: boolean
  organization?: {
    id: number
    name: string
    industry?: string
    api_url?: string
    has_api_key: boolean
    created_at: string
  }
}


// ─── Data Pipeline API helpers ────────────────────────────

export const dataApi = {
  // Sources
  getSources: () => api<DataSource[]>('/data/sources'),
  createSource: (payload: Record<string, unknown>) =>
    api<DataSource>('/data/sources', { method: 'POST', body: JSON.stringify(payload) }),
  updateSource: (id: number, payload: Record<string, unknown>) =>
    api<DataSource>(`/data/sources/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  deleteSource: (id: number) =>
    api<{ detail: string }>(`/data/sources/${id}`, { method: 'DELETE' }),
  getSourcesSummary: () => api<MultiSourceSummary>('/data/sources/summary'),
  refreshSource: (id: number) =>
    api<{ detail: string; row_count: number }>(`/data/sources/${id}/refresh`, { method: 'POST' }),

  // Records (pipeline)
  queryRecords: (params: Record<string, unknown>) =>
    api<PaginatedRecords>('/data/records', { method: 'POST', body: JSON.stringify(params) }),

  // Field config
  getFieldConfigs: (sourceId: number) =>
    api<FieldConfig[]>(`/data/sources/${sourceId}/fields`),
  updateFieldConfigs: (sourceId: number, configs: Record<string, unknown>[]) =>
    api<FieldConfig[]>(`/data/sources/${sourceId}/fields`, {
      method: 'PUT', body: JSON.stringify({ configs }),
    }),

  // Email
  getEmailTemplates: () => api<EmailTemplate[]>('/data/email/templates'),
  createEmailTemplate: (payload: Record<string, unknown>) =>
    api<EmailTemplate>('/data/email/templates', { method: 'POST', body: JSON.stringify(payload) }),
  deleteEmailTemplate: (id: number) =>
    api<{ detail: string }>(`/data/email/templates/${id}`, { method: 'DELETE' }),
  sendEmails: (payload: Record<string, unknown>) =>
    api<{ total_recipients: number; queued: number; failed: number; details: unknown[] }>(
      '/data/email/send', { method: 'POST', body: JSON.stringify(payload) },
    ),

  // Analytics
  runAnalytics: (payload: Record<string, unknown>) =>
    api<AnalyticsResult>('/data/analytics', { method: 'POST', body: JSON.stringify(payload) }),
  fieldAnalytics: (sourceId: number, fieldKey: string) =>
    api<Record<string, unknown>>(`/data/analytics/${sourceId}/field/${fieldKey}`),

  // Action log
  getActions: (limit = 50) => api<ActionLog[]>(`/data/actions?limit=${limit}`),
}
