import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  Brain, LayoutDashboard, MessageSquare, Map, BarChart2, User,
  FileQuestion, Mic, LogOut, Menu, X, Zap, Sun, Moon,
  RefreshCw, ChevronDown, Target,
} from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuthStore } from '@/store/authStore'
import { useThemeStore } from '@/store/themeStore'

const NAV_ITEMS = [
  { to: '/dashboard',           label: 'Dashboard',        icon: LayoutDashboard, end: true, color: 'text-indigo-400' },
  { to: '/dashboard/chat',      label: 'AI Mentor',        icon: MessageSquare,              color: 'text-cyan-400'   },
  { to: '/dashboard/skills',    label: 'Skill Gap',        icon: Target,                     color: 'text-rose-400'   },
  { to: '/dashboard/roadmap',   label: 'My Roadmap',       icon: Map,                        color: 'text-purple-400' },
  { to: '/dashboard/analytics', label: 'Analytics',        icon: BarChart2,                  color: 'text-pink-400'   },
  { to: '/dashboard/quiz',      label: 'Quiz',             icon: FileQuestion,               color: 'text-amber-400'  },
  { to: '/dashboard/whatif',    label: 'What-If Simulator',icon: Zap,                        color: 'text-emerald-400'},
  { to: '/dashboard/interview', label: 'Mock Interview',   icon: Mic,                        color: 'text-sky-400'    },
  { to: '/dashboard/profile',   label: 'Profile',          icon: User,                       color: 'text-gray-400'   },
]

export default function DashboardLayout() {
  const { user, logout } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const handleSwitchAccount = () => {
    logout()
    navigate('/login')
  }

  const avatar = user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'

  const SidebarContent = () => (
    <aside
      className="w-64 h-screen flex flex-col fixed left-0 top-0 z-40"
      style={{ background: 'var(--sidebar-bg)', borderRight: '1px solid var(--sidebar-border)' }}
    >
      {/* Logo */}
      <div className="p-5 flex items-center justify-between" style={{ borderBottom: '1px solid var(--sidebar-border)' }}>
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-glow">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold gradient-text text-sm">NeuraLearn</span>
            <span className="block text-[10px] text-muted" style={{ color: 'var(--text-muted)' }}>AI Learning Engine</span>
          </div>
        </div>
        <button onClick={() => setSidebarOpen(false)} className="text-gray-500 lg:hidden hover:text-white transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto scrollbar-thin">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end, color }) => (
          <NavLink
            key={to} to={to} end={end}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) => isActive ? 'sidebar-item-active' : 'sidebar-item'}
          >
            <Icon className={`w-4 h-4 flex-shrink-0 ${color}`} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Theme toggle */}
      <div className="px-3 pb-1">
        <button
          onClick={toggleTheme}
          className="sidebar-item w-full group"
          title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          <div className="w-8 h-4 rounded-full relative flex items-center px-0.5 transition-colors duration-300"
            style={{ background: theme === 'dark' ? 'rgba(99,102,241,0.4)' : 'rgba(245,158,11,0.4)' }}>
            <motion.div
              layout
              className="w-3 h-3 rounded-full bg-white shadow-sm"
              animate={{ x: theme === 'dark' ? 0 : 16 }}
              transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            />
          </div>
          {theme === 'dark'
            ? <><Moon className="w-4 h-4 text-indigo-400" /><span>Dark Mode</span></>
            : <><Sun  className="w-4 h-4 text-amber-400"  /><span>Light Mode</span></>
          }
        </button>
      </div>

      {/* User panel */}
      <div className="p-3" style={{ borderTop: '1px solid var(--sidebar-border)' }}>
        <button
          onClick={() => setUserMenuOpen(o => !o)}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 hover:bg-indigo-500/10"
        >
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-sm font-bold text-white flex-shrink-0 shadow-glow">
            {avatar}
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
              {user?.full_name || user?.username}
            </p>
            <p className="text-xs truncate" style={{ color: 'var(--text-muted)' }}>{user?.email}</p>
          </div>
          <ChevronDown className={`w-3.5 h-3.5 flex-shrink-0 transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`}
            style={{ color: 'var(--text-muted)' }} />
        </button>

        <AnimatePresence>
          {userMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden mt-1 space-y-0.5"
            >
              <button
                onClick={handleSwitchAccount}
                className="sidebar-item w-full text-indigo-400 hover:text-indigo-300"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Switch Account</span>
              </button>
              <button
                onClick={handleLogout}
                className="sidebar-item w-full text-rose-400 hover:text-rose-300"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign Out</span>
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </aside>
  )

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-base)' }}>
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <SidebarContent />
      </div>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <div className="lg:hidden fixed inset-0 z-40 flex">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/70 backdrop-blur-sm"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.div
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            >
              <SidebarContent />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main className="flex-1 lg:ml-64 min-h-screen flex flex-col">
        {/* Mobile top bar */}
        <header
          className="lg:hidden flex items-center justify-between p-4"
          style={{ background: 'var(--sidebar-bg)', borderBottom: '1px solid var(--sidebar-border)' }}
        >
          <button onClick={() => setSidebarOpen(true)} className="p-1.5 rounded-lg hover:bg-white/10 transition-colors">
            <Menu className="w-5 h-5" style={{ color: 'var(--text-muted)' }} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
              <Brain className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="font-bold gradient-text text-sm">NeuraLearn AI</span>
          </div>
          <button onClick={toggleTheme} className="p-1.5 rounded-lg hover:bg-white/10 transition-colors">
            {theme === 'dark'
              ? <Sun  className="w-4 h-4 text-amber-400" />
              : <Moon className="w-4 h-4 text-indigo-400" />
            }
          </button>
        </header>

        <div className="flex-1 p-4 md:p-6 overflow-auto scrollbar-thin">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
