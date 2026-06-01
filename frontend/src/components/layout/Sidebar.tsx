import { NavLink } from 'react-router-dom'

const tabs = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/users', label: 'Organization Users', icon: '☰' },
  { to: '/sources', label: 'Data Sources', icon: '⛁' },
  { to: '/analytics', label: 'Analytics', icon: '📊' },
  { to: '/email', label: 'Email Center', icon: '✉' },
  { to: '/chat', label: 'AI Chat', icon: '💬' },
  { to: '/content', label: 'Content AI', icon: '✎' },
]

export default function Sidebar() {
  return (
    <aside
      className="glass"
      style={{
        width: 240,
        minHeight: '100vh',
        padding: '20px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        borderRight: '1px solid rgba(255,255,255,0.05)',
        flexShrink: 0,
      }}
    >
      <div style={{ padding: '8px 12px 20px' }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 12,
            background: 'linear-gradient(135deg,#7c3aed,#4f46e5)',
            display: 'grid',
            placeItems: 'center',
            fontWeight: 800,
            marginBottom: 8,
          }}
        >
          N
        </div>
        <div className="gradient-text" style={{ fontWeight: 700, fontSize: 18 }}>
          NexusAI
        </div>
        <div style={{ fontSize: 12, color: '#6b7280' }}>Smart User Intelligence</div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '10px 12px',
              borderRadius: 10,
              color: isActive ? '#c4b5fd' : '#9ca3af',
              background: isActive ? 'rgba(124,58,237,0.15)' : 'transparent',
              fontWeight: isActive ? 600 : 500,
              fontSize: 14,
              borderLeft: isActive ? '3px solid #7c3aed' : '3px solid transparent',
            })}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
