import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import LandingPage from '@/pages/LandingPage'
import LoginPage from '@/pages/LoginPage'
import RegisterPage from '@/pages/RegisterPage'
import OnboardingPage from '@/pages/OnboardingPage'
import DashboardLayout from '@/components/dashboard/DashboardLayout'
import DashboardPage from '@/pages/DashboardPage'
import ChatPage from '@/pages/ChatPage'
import RoadmapPage from '@/pages/RoadmapPage'
import AnalyticsPage from '@/pages/AnalyticsPage'
import ProfilePage from '@/pages/ProfilePage'
import QuizPage from '@/pages/QuizPage'
import InterviewPage from '@/pages/InterviewPage'
import WhatIfPage from '@/pages/WhatIfPage'
import SkillGapPage from '@/pages/SkillGapPage'
import { Brain } from 'lucide-react'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (isAuthenticated) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}

/** Full-page spinner shown while the initial session restore is in progress */
function AppLoadingScreen() {
  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center gap-4 z-50"
      style={{ background: 'var(--bg-base)' }}
    >
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
        <Brain className="w-7 h-7 text-white" />
      </div>
      <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-sm text-gray-500">Loading your learning profile…</p>
    </div>
  )
}

export default function App() {
  const { isAuthenticated, isProfileLoading, fetchMe } = useAuthStore()

  useEffect(() => {
    // Restore session on app load if a token is stored
    const token = localStorage.getItem('access_token')
    if (token && !isAuthenticated) {
      fetchMe().catch(() => {})
    }
  }, [])

  // While we're restoring the session (token exists but profile not yet loaded),
  // show a loading screen so protected pages don't flash with null profile.
  const token = localStorage.getItem('access_token')
  if (token && isAuthenticated && isProfileLoading) {
    return <AppLoadingScreen />
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

        {/* Protected */}
        <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
        <Route
          path="/dashboard"
          element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}
        >
          <Route index element={<DashboardPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="roadmap" element={<RoadmapPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="quiz" element={<QuizPage />} />
          <Route path="interview" element={<InterviewPage />} />
          <Route path="whatif" element={<WhatIfPage />} />
          <Route path="skills" element={<SkillGapPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
