import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function ProtectedRoute({ requireOnboarding = true }: { requireOnboarding?: boolean }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', color: '#9ca3af' }}>
        Loading...
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  if (requireOnboarding && !user.onboarding_completed) {
    return <Navigate to="/onboarding" replace />
  }

  return <Outlet />
}

export function OnboardingRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>Loading...</div>
  }

  if (!user) return <Navigate to="/login" replace />
  if (user.onboarding_completed) return <Navigate to="/dashboard" replace />

  return <Outlet />
}
