import { Outlet, NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Target, Bot, Layers, Calendar,
  BarChart3, Brain, Settings, Zap, ChevronRight, Stethoscope
} from 'lucide-react'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/missions',  icon: Target,          label: 'Missions' },
  { to: '/agents',    icon: Bot,             label: 'Agents' },
  { to: '/brands',    icon: Layers,          label: 'Brands' },
  { to: '/calendar',  icon: Calendar,        label: 'Calendar' },
  { to: '/analytics', icon: BarChart3,       label: 'Analytics' },
  { to: '/knowledge', icon: Brain,           label: 'Knowledge' },
  { to: '/doctor',    icon: Stethoscope,     label: 'Runtime Doctor' },
  { to: '/settings',  icon: Settings,        label: 'Settings' },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--color-surface-900)' }}>
      {/* ── Sidebar ──────────────────────────────────────────── */}
      <aside
        className="w-64 flex-shrink-0 flex flex-col border-r"
        style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'var(--color-surface-800)' }}
      >
        {/* Logo */}
        <div className="px-6 py-5 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center glow-brand"
              style={{ background: 'linear-gradient(135deg, #3b6bff, #9b59ff)' }}
            >
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-white leading-none">Animus Studio</p>
              <p className="text-[10px] mt-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
                Project Hermes v0.1
              </p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 cursor-pointer group ${
                  isActive
                    ? 'nav-active font-medium'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                }`
              }
            >
              <Icon size={16} className="flex-shrink-0" />
              <span className="flex-1">{label}</span>
              <ChevronRight
                size={12}
                className="opacity-0 group-hover:opacity-40 transition-opacity"
              />
            </NavLink>
          ))}
        </nav>

        {/* Status bar */}
        <div
          className="px-4 py-3 border-t text-xs"
          style={{ borderColor: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.3)' }}
        >
          <div className="flex items-center gap-2">
            <span className="pulse-dot" style={{ background: '#00e5a0' }} />
            <span>Executive Agent: Idle</span>
          </div>
        </div>
      </aside>

      {/* ── Main ─────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
