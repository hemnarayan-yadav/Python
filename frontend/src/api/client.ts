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
