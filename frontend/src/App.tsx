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
import { Brain, Loader2 } from 'lucide-react'

// ─── Loading overlay (always INSIDE BrowserRouter) ────────────────────────────

function AppLoadingOverlay() {
  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center gap-4 z-50"
      style={{ background: 'var(--bg-base)' }}
    >
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
        <Brain className="w-7 h-7 text-white" />
      </div>
      <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      <p className="text-sm text-gray-500">Loading your learning profile…</p>
    </div>
  )
}

// ─── Route guards ─────────────────────────────────────────────────────────────

/**
 * ProtectedRoute: requires authentication.
 * If not authenticated and no auth is in flight, redirect to /login.
 * If auth is still loading, render nothing (AppLoadingOverlay is shown by AppRoutes).
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, isProfileLoading } = useAuthStore()

  // Still resolving auth — don't redirect prematurely
  if (isLoading || isProfileLoading) return null

  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

/**
 * PublicRoute: only accessible to unauthenticated users.
 *
 * KEY FIX: Do NOT redirect while auth is in flight (isLoading or isProfileLoading).
 * Previously, PublicRoute redirected as soon as isAuthenticated turned true, which
 * happened mid-way through register()/login() before the flow was complete.
 * This caused RegisterPage to unmount before navigate('/onboarding') could run.
 *
 * When auth is fully settled:
 *   - authenticated + no profile → /onboarding (new user path)
 *   - authenticated + has profile → /dashboard  (returning user path)
 */
function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, isProfileLoading, profile } = useAuthStore()

  // Auth operation still in flight — render nothing, loading overlay is shown
  if (isLoading || isProfileLoading) return null

  if (isAuthenticated) {
    // New user: no profile yet → send to onboarding
    // Returning user: has profile → send to dashboard
    return <Navigate to={profile ? '/dashboard' : '/onboarding'} replace />
  }

  return <>{children}</>
}

// ─── Inner routes (needs to be a separate component so useEffect is inside Router) ─

function AppRoutes() {
  const { isLoading, isProfileLoading, fetchMe } = useAuthStore()

  useEffect(() => {
    // Always re-validate the stored token on every page load/refresh.
    // No isAuthenticated guard here — that value is stale from Zustand persist.
    const token = localStorage.getItem('access_token')
    if (token) {
      fetchMe().catch(() => {})
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const token = localStorage.getItem('access_token')
  const isRestoring = token && (isLoading || isProfileLoading)

  return (
    <>
      {/* Loading overlay sits INSIDE the router — BrowserRouter stays mounted */}
      {isRestoring && <AppLoadingOverlay />}

      <Routes>
        {/* Public */}
        <Route path="/"         element={<LandingPage />} />
        <Route path="/login"    element={<PublicRoute><LoginPage /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

        {/* Protected */}
        <Route path="/onboarding" element={<ProtectedRoute><OnboardingPage /></ProtectedRoute>} />
        <Route
          path="/dashboard"
          element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}
        >
          <Route index          element={<DashboardPage />} />
          <Route path="chat"      element={<ChatPage />} />
          <Route path="roadmap"   element={<RoadmapPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="profile"   element={<ProfilePage />} />
          <Route path="quiz"      element={<QuizPage />} />
          <Route path="interview" element={<InterviewPage />} />
          <Route path="whatif"    element={<WhatIfPage />} />
          <Route path="skills"    element={<SkillGapPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

// ─── Root ─────────────────────────────────────────────────────────────────────

/**
 * BrowserRouter is rendered UNCONDITIONALLY here — it must never be
 * conditionally unmounted. Doing so destroys the router history stack
 * and causes blank screens / broken navigate() calls.
 */
export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
