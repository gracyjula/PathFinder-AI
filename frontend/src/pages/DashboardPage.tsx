import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import { Flame, Target, BookOpen, Trophy, ArrowRight, Zap, Brain, TrendingUp, Lightbulb, ChevronRight, AlertTriangle, Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { DashboardStats, NextBestAction, SkillGapReport } from '@/types'

export default function DashboardPage() {
  const { user, profile, fetchProfile } = useAuthStore()
  const qc = useQueryClient()

  const demoSeedMutation = useMutation({
    mutationFn: () => api.post('/analytics/demo-seed'),
    onSuccess: async () => {
      // Re-fetch profile so authStore.profile reflects the new career_goal,
      // which unblocks enabled: !!profile?.career_goal queries in other pages.
      await fetchProfile()
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['mastery'] })
      qc.invalidateQueries({ queryKey: ['skill-gap-current'] })
      qc.invalidateQueries({ queryKey: ['next-best-action'] })
      toast.success('🎯 Demo persona seeded! AI Engineer, 8h/wk, Python 90% → MLOps 10%')
    },
    onError: () => toast.error('Seed failed — complete onboarding first'),
  })

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/analytics/dashboard').then(r => r.data),
  })

  const { data: nbaData } = useQuery<NextBestAction[]>({
    queryKey: ['next-best-action'],
    queryFn: () => api.get('/analytics/next-best-action').then(r => r.data),
    enabled: !!profile?.career_goal,
  })

  const { data: gapData } = useQuery<SkillGapReport>({
    queryKey: ['skill-gap-current'],
    queryFn: () => api.get('/analytics/skill-gap').then(r => r.data),
    enabled: !!profile?.career_goal,
    retry: false,
  })

  const { data: masteryData } = useQuery<{ mastery: Record<string, number> }>({
    queryKey: ['mastery'],
    queryFn: () => api.get('/analytics/mastery').then(r => r.data),
    enabled: !!profile,
  })

  // Skill radar data — from mastery map if available, else from gap report
  const radarData: { name: string; value: number }[] = masteryData?.mastery
    ? Object.entries(masteryData.mastery)
        .sort(([, a], [, b]) => b - a)
        .slice(0, 7)
        .map(([name, value]) => ({ name, value: Math.round(value) }))
    : gapData?.skill_scores
    ? Object.entries(gapData.skill_scores)
        .slice(0, 7)
        .map(([name, value]) => ({ name, value: Math.round(value as number) }))
    : []

  // Milestone progress bar chart — real completed vs total per roadmap
  const milestoneBarData = stats?.roadmaps?.map(r => ({
    name: r.title.length > 18 ? r.title.slice(0, 16) + '…' : r.title,
    progress: r.completion_percentage,
  })) ?? []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const readiness = gapData?.career_readiness_pct ?? stats?.profile.career_readiness_score ?? 0
  const topNba = nbaData?.[0]

  return (
    <div className="max-w-7xl mx-auto">
      {/* Greeting */}
      <div className="mb-8 flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">
            Welcome back, <span className="gradient-text">{user?.full_name?.split(' ')[0] || user?.username}</span> 👋
          </h1>
          <p className="text-gray-400 text-sm">
            {profile?.career_goal
              ? `You're on track to become a ${profile.career_goal}`
              : 'Complete your profile to get started'}
          </p>
        </div>
        {/* Demo seed button — for judges/demos */}
        <button
          onClick={() => demoSeedMutation.mutate()}
          disabled={demoSeedMutation.isPending}
          className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5 opacity-60 hover:opacity-100"
          title="Seed demo persona: AI Engineer, Python 90%, MLOps 10%"
        >
          {demoSeedMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : '🎯'}
          Demo Seed
        </button>
      </div>

      {/* ── NEXT BEST ACTION ─────────────────────────────────────────── */}
      {topNba && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-5 mb-6 border border-primary-500/30 bg-gradient-to-r from-primary-500/10 to-accent-500/10"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 flex-1">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Lightbulb className="w-4 h-4 text-white" />
              </div>
              <div>
                <p className="text-xs font-semibold text-primary-400 uppercase tracking-wide mb-1">Next Best Action</p>
                <p className="font-semibold text-white">
                  {topNba.type === 'prerequisite' ? '🔗 Prerequisite: ' : '🎯 Focus on: '}
                  <span className="gradient-text">{topNba.skill}</span>
                  {topNba.estimated_hours > 0 && (
                    <span className="text-gray-400 font-normal ml-2 text-sm">~{topNba.estimated_hours}h</span>
                  )}
                </p>
                <p className="text-sm text-gray-400 mt-1">{topNba.reason}</p>
              </div>
            </div>
            <div className="flex gap-2 flex-shrink-0">
              <Link
                to="/dashboard/quiz"
                state={{ prefillTopic: topNba.skill }}
                className="btn-primary text-sm py-2 px-4 flex items-center gap-1.5"
              >
                Take Quiz <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
          {/* All actions */}
          {nbaData && nbaData.length > 1 && (
            <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-2">
              {nbaData.slice(1).map((a, i) => (
                <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-white/5 text-gray-400">
                  {a.skill}
                </span>
              ))}
            </div>
          )}
        </motion.div>
      )}

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Flame className="w-5 h-5 text-orange-400" />}
          label="Day Streak"
          value={stats?.streak.current_streak || 0}
          sub={`Best: ${stats?.streak.longest_streak || 0} days`}
          cls="stat-amber"
        />
        <StatCard
          icon={<BookOpen className="w-5 h-5 text-cyan-400" />}
          label="Milestones"
          value={`${stats?.milestones.completed || 0}/${stats?.milestones.total || 0}`}
          sub={`${stats?.milestones.percentage || 0}% complete`}
          cls="stat-blue"
        />
        <StatCard
          icon={<Trophy className="w-5 h-5 text-yellow-400" />}
          label="Quiz Avg"
          value={`${stats?.quizzes.avg_score || 0}%`}
          sub={`${stats?.quizzes.count || 0} quizzes taken`}
          cls="stat-green"
        />
        <StatCard
          icon={<Target className="w-5 h-5 text-purple-400" />}
          label="Career Ready"
          value={`${Math.round(readiness)}%`}
          sub={readiness >= 70 ? 'Interview ready!' : 'Keep going!'}
          cls="stat-purple"
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-8">
        {/* Career Readiness Meter */}
        <div className="glass-card p-6">
          <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary-400" /> Career Readiness
          </h2>
          <div className="relative flex items-center justify-center mb-4">
            <svg viewBox="0 0 100 60" className="w-40">
              <path d="M 10 50 A 40 40 0 0 1 90 50" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" strokeLinecap="round" />
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke="url(#readinessGrad)"
                strokeWidth="8"
                strokeLinecap="round"
                strokeDasharray={`${(readiness / 100) * 125.6} 125.6`}
              />
              <defs>
                <linearGradient id="readinessGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#4c6ef5" />
                  <stop offset="100%" stopColor="#cc33f0" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute bottom-0 text-center">
              <div className="text-3xl font-bold gradient-text">{Math.round(readiness)}</div>
              <div className="text-xs text-gray-400">/ 100</div>
            </div>
          </div>
          {gapData && (
            <div className="space-y-1.5 text-xs">
              {gapData.strong_skills.length > 0 && (
                <p className="text-green-400">✅ Strong: {gapData.strong_skills.slice(0, 3).join(', ')}</p>
              )}
              {gapData.gap_skills.length > 0 && (
                <p className="text-red-400">⚠️ Gaps: {gapData.gap_skills.slice(0, 3).join(', ')}</p>
              )}
            </div>
          )}
          <Link to="/dashboard/analytics" className="text-primary-400 text-sm flex items-center gap-1 hover:text-primary-300 mt-3">
            Full analysis <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Skill Radar — real mastery data */}
        <div className="glass-card p-6">
          <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-400" /> Skill Mastery
          </h2>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                <Radar name="Mastery" dataKey="value" stroke="#4c6ef5" fill="#4c6ef5" fillOpacity={0.25} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-44 text-center">
              <AlertTriangle className="w-8 h-8 text-gray-600 mb-2" />
              <p className="text-sm text-gray-500">Complete onboarding to see your skill radar</p>
            </div>
          )}
        </div>

        {/* Roadmap Progress — real data */}
        <div className="glass-card p-6">
          <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary-400" /> Roadmap Progress
          </h2>
          {milestoneBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={milestoneBarData} layout="vertical">
                <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} axisLine={false} tickLine={false} width={70} />
                <Tooltip
                  formatter={(val: number) => [`${val}%`, 'Complete']}
                  contentStyle={{ background: '#1e1b4b', border: '1px solid #4c6ef5', borderRadius: '8px', color: '#e0e7ff', fontSize: 12 }}
                />
                <Bar dataKey="progress" radius={[0, 4, 4, 0]}>
                  {milestoneBarData.map((_, i) => (
                    <Cell key={i} fill={`hsl(${220 + i * 30}, 70%, 60%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex flex-col items-center justify-center h-44 text-center">
              <Target className="w-8 h-8 text-gray-600 mb-2" />
              <p className="text-sm text-gray-500">Generate a roadmap to track progress</p>
              <Link to="/dashboard/roadmap" className="text-primary-400 text-xs mt-2 hover:underline">Create roadmap →</Link>
            </div>
          )}
        </div>
      </div>

      {/* Active Roadmaps */}
      {stats?.roadmaps && stats.roadmaps.length > 0 && (
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-white">Active Roadmaps</h2>
            <Link to="/dashboard/roadmap" className="text-primary-400 text-sm hover:text-primary-300 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-4">
            {stats.roadmaps.map(r => (
              <div key={r.id} className="flex items-center justify-between">
                <span className="text-gray-300 text-sm truncate flex-1">{r.title}</span>
                <div className="flex items-center gap-3 ml-4">
                  <div className="w-32 bg-white/5 rounded-full h-1.5">
                    <motion.div
                      className="bg-gradient-to-r from-primary-500 to-accent-500 h-1.5 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${r.completion_percentage}%` }}
                      transition={{ duration: 0.8, ease: 'easeOut' }}
                    />
                  </div>
                  <span className="text-xs text-gray-400 w-10 text-right">{r.completion_percentage}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { to: '/dashboard/chat',   label: 'Chat with AI Mentor',    icon: Brain,   color: 'from-blue-500 to-cyan-500'    },
          { to: '/dashboard/skills', label: 'Skill Gap Analysis',     icon: Target,  color: 'from-rose-500 to-pink-500'    },
          { to: '/dashboard/quiz',   label: 'Take a Quiz',            icon: Trophy,  color: 'from-yellow-500 to-orange-500'},
          { to: '/dashboard/whatif', label: 'What-If Simulator',      icon: Zap,     color: 'from-green-500 to-emerald-500'},
        ].map(action => (
          <Link key={action.to} to={action.to}
            className="glass-card-hover p-5 flex flex-col items-start gap-3 group">
            <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${action.color} flex items-center justify-center`}>
              <action.icon className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-medium text-gray-300 group-hover:text-white">{action.label}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, sub, cls }: {
  icon: React.ReactNode; label: string; value: string | number; sub: string; cls: string
}) {
  return (
    <div className={`glass-card p-5 rounded-2xl ${cls}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>{label}</span>
        {icon}
      </div>
      <div className="text-2xl font-bold mb-0.5" style={{ color: 'var(--text-primary)' }}>{value}</div>
      <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{sub}</div>
    </div>
  )
}
