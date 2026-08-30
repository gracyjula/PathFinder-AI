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
    // Always re-validate the token on every page load / refresh.
    //
    // BUG FIXED: previously this was guarded by `!isAuthenticated`, which meant
    // that after a page refresh where Zustand had persisted isAuthenticated=true,
    // fetchMe() was never called — leaving isProfileLoading=true forever and
    // the entire app stuck on the loading screen.
    //
    // Now: if a token exists we always call fetchMe(), which:
    //   1. verifies the token against the backend (/auth/me)
    //   2. fetches the latest profile
    //   3. sets isProfileLoading=false when done (success or failure)
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchMe().catch(() => {})
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Show the loading screen only while we're actively restoring the session.
  // isProfileLoading is set to true at the start of fetchMe() and back to false
  // when it resolves — so this spinner is always time-bounded.
  const token = localStorage.getItem('access_token')
  if (token && isProfileLoading) {
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
