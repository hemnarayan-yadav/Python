import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { useAuth } from '../../context/AuthContext'
import { OrgRecordsProvider, useOrgRecords } from '../../context/OrgRecordsContext'

function LayoutInner() {
  const { user, logout } = useAuth()
  const { refresh } = useOrgRecords()

  useEffect(() => {
    refresh()
  }, [refresh])

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <header
          className="glass"
          style={{
            padding: '14px 24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
          }}
        >
          <div style={{ fontSize: 14, color: '#9ca3af' }}>
            {user?.organization?.name ?? 'Organization'}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 14, color: '#c4b5fd' }}>{user?.email}</span>
            <button type="button" className="btn-ghost" onClick={logout} style={{ fontSize: 13 }}>
              Logout
            </button>
          </div>
        </header>
        <main style={{ padding: 24, flex: 1, overflow: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default function AppLayout() {
  return (
    <OrgRecordsProvider>
      <LayoutInner />
    </OrgRecordsProvider>
  )
}
