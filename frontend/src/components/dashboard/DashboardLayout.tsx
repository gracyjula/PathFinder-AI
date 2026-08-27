import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { Brain, LayoutDashboard, MessageSquare, Map, BarChart2, User, FileQuestion, Mic, LogOut, Menu, X, Zap } from 'lucide-react'
import { useState } from 'react'
import { useAuthStore } from '@/store/authStore'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/dashboard/chat', label: 'AI Mentor', icon: MessageSquare },
  { to: '/dashboard/roadmap', label: 'My Roadmap', icon: Map },
  { to: '/dashboard/analytics', label: 'Analytics', icon: BarChart2 },
  { to: '/dashboard/quiz', label: 'Quiz', icon: FileQuestion },
  { to: '/dashboard/whatif', label: 'What-If Simulator', icon: Zap },
  { to: '/dashboard/interview', label: 'Mock Interview', icon: Mic },
  { to: '/dashboard/profile', label: 'Profile', icon: User },
]

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const Sidebar = () => (
    <aside className="w-64 h-screen flex flex-col bg-[#0d0d24] border-r border-white/5 fixed left-0 top-0 z-40">
      {/* Logo */}
      <div className="p-5 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold gradient-text">NeuraLearn AI</span>
        </div>
        <button onClick={() => setSidebarOpen(false)} className="text-gray-500 lg:hidden">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto scrollbar-thin">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => isActive ? 'sidebar-item-active' : 'sidebar-item'}
            onClick={() => setSidebarOpen(false)}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            <span className="text-sm font-medium">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User info */}
      <div className="p-4 border-t border-white/5">
        <div className="flex items-center gap-3 mb-3 px-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
            {user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name || user?.username}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
        </div>
        <button onClick={handleLogout} className="sidebar-item w-full text-red-400 hover:text-red-300 hover:bg-red-500/10">
          <LogOut className="w-4 h-4" />
          <span className="text-sm font-medium">Sign Out</span>
        </button>
      </div>
    </aside>
  )

  return (
    <div className="flex min-h-screen bg-[#0a0a1a]">
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-black/60" onClick={() => setSidebarOpen(false)} />
          <Sidebar />
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 lg:ml-64 min-h-screen flex flex-col">
        {/* Mobile header */}
        <header className="lg:hidden flex items-center justify-between p-4 border-b border-white/5 bg-[#0d0d24]">
          <button onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5 text-gray-400" />
          </button>
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary-400" />
            <span className="font-bold gradient-text text-sm">NeuraLearn AI</span>
          </div>
          <div className="w-5" />
        </header>

        <div className="flex-1 p-6 overflow-auto scrollbar-thin">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
