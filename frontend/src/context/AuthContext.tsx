import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, clearToken, getToken, setToken, type AuthUser } from '../api/client'

type AuthContextValue = {
  user: AuthUser | null
  loading: boolean
  login: (email: string, password: string) => Promise<boolean>
  register: (payload: {
    name: string
    email: string
    password: string
    age: number
  }) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  completeOnboarding: (payload: {
    name: string
    industry?: string
    api_url?: string
    api_key?: string
  }) => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    const token = getToken()
    if (!token) {
      setUser(null)
      return
    }
    const profile = await api<AuthUser>('/auth/me')
    setUser(profile)
  }, [])

  useEffect(() => {
    ;(async () => {
      try {
        await refreshUser()
      } catch {
        clearToken()
        setUser(null)
      } finally {
        setLoading(false)
      }
    })()
  }, [refreshUser])

  const login = useCallback(async (email: string, password: string) => {
    const data = await api<{ access_token: string; onboarding_completed: boolean }>(
      '/auth/login',
      { method: 'POST', body: JSON.stringify({ email, password }) },
    )
    setToken(data.access_token)
    await refreshUser()
    return data.onboarding_completed
  }, [refreshUser])

  const register = useCallback(
    async (payload: { name: string; email: string; password: string; age: number }) => {
      const data = await api<{
        access_token: string
        onboarding_completed: boolean
        user: AuthUser
      }>('/auth/register', { method: 'POST', body: JSON.stringify(payload) })
      setToken(data.access_token)
      setUser(data.user)
    },
    [],
  )

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const completeOnboarding = useCallback(
    async (payload: {
      name: string
      industry?: string
      api_url?: string
      api_key?: string
    }) => {
      await api('/organization/setup', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      await refreshUser()
    },
    [refreshUser],
  )

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      register,
      logout,
      refreshUser,
      completeOnboarding,
    }),
    [user, loading, login, register, logout, refreshUser, completeOnboarding],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
