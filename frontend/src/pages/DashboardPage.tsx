import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts'
import { Flame, Target, BookOpen, Trophy, ArrowRight, Zap, Brain, TrendingUp } from 'lucide-react'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { DashboardStats } from '@/types'

export default function DashboardPage() {
  const { user, profile } = useAuthStore()

  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/analytics/dashboard').then(r => r.data),
  })

  const radarData = profile?.skill_gap_report?.skill_scores
    ? Object.entries(profile.skill_gap_report.skill_scores).slice(0, 6).map(([name, value]) => ({ name, value }))
    : [
        { name: 'Python', value: 75 }, { name: 'ML', value: 60 }, { name: 'Deep Learning', value: 30 },
        { name: 'NLP', value: 20 }, { name: 'MLOps', value: 15 }, { name: 'LangChain', value: 10 },
      ]

  const progressData = [
    { month: 'Jul', progress: 10 }, { month: 'Aug', progress: 25 }, { month: 'Sep', progress: 40 },
    { month: 'Oct', progress: 55 }, { month: 'Nov', progress: 65 }, { month: 'Dec', progress: stats?.milestones.percentage || 70 },
  ]

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const readiness = stats?.profile.career_readiness_score || 0

  return (
    <div className="max-w-7xl mx-auto">
      {/* Greeting */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-1">
          Welcome back, <span className="gradient-text">{user?.full_name?.split(' ')[0] || user?.username}</span> 👋
        </h1>
        <p className="text-gray-400 text-sm">
          {profile?.career_goal ? `You're on track to become a ${profile.career_goal}` : 'Complete your profile to get started'}
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Flame className="w-5 h-5 text-orange-400" />}
          label="Day Streak"
          value={stats?.streak.current_streak || 0}
          sub={`Best: ${stats?.streak.longest_streak || 0} days`}
          color="from-orange-500/20 to-red-500/20"
        />
        <StatCard
          icon={<BookOpen className="w-5 h-5 text-blue-400" />}
          label="Milestones"
          value={`${stats?.milestones.completed || 0}/${stats?.milestones.total || 0}`}
          sub={`${stats?.milestones.percentage || 0}% complete`}
          color="from-blue-500/20 to-cyan-500/20"
        />
        <StatCard
          icon={<Trophy className="w-5 h-5 text-yellow-400" />}
          label="Quiz Avg"
          value={`${stats?.quizzes.avg_score || 0}%`}
          sub={`${stats?.quizzes.count || 0} quizzes taken`}
          color="from-yellow-500/20 to-amber-500/20"
        />
        <StatCard
          icon={<Target className="w-5 h-5 text-purple-400" />}
          label="Career Ready"
          value={`${readiness}%`}
          sub={readiness >= 70 ? 'Interview ready!' : 'Keep going!'}
          color="from-purple-500/20 to-pink-500/20"
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
              <div className="text-3xl font-bold gradient-text">{readiness}</div>
              <div className="text-xs text-gray-400">/ 100</div>
            </div>
          </div>
          <Link to="/dashboard/analytics" className="text-primary-400 text-sm flex items-center gap-1 hover:text-primary-300">
            View breakdown <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Skill Radar */}
        <div className="glass-card p-6">
          <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Zap className="w-4 h-4 text-accent-400" /> Skill Radar
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
              <Radar name="Skills" dataKey="value" stroke="#4c6ef5" fill="#4c6ef5" fillOpacity={0.2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Progress Chart */}
        <div className="glass-card p-6">
          <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary-400" /> Learning Progress
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={progressData}>
              <defs>
                <linearGradient id="progressGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4c6ef5" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#4c6ef5" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="month" tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis hide />
              <Tooltip contentStyle={{ background: '#1e1b4b', border: '1px solid #4c6ef5', borderRadius: '8px', color: '#e0e7ff' }} />
              <Area type="monotone" dataKey="progress" stroke="#4c6ef5" fill="url(#progressGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
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
                    <div className="bg-gradient-to-r from-primary-500 to-accent-500 h-1.5 rounded-full"
                      style={{ width: `${r.completion_percentage}%` }} />
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
          { to: '/dashboard/chat', label: 'Chat with AI Mentor', icon: Brain, color: 'from-blue-500 to-cyan-500' },
          { to: '/dashboard/roadmap', label: 'View Roadmap', icon: Target, color: 'from-purple-500 to-pink-500' },
          { to: '/dashboard/quiz', label: 'Take a Quiz', icon: Trophy, color: 'from-yellow-500 to-orange-500' },
          { to: '/dashboard/interview', label: 'Mock Interview', icon: Zap, color: 'from-green-500 to-emerald-500' },
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

function StatCard({ icon, label, value, sub, color }: {
  icon: React.ReactNode; label: string; value: string | number; sub: string; color: string
}) {
  return (
    <div className={`glass-card p-5 bg-gradient-to-br ${color}`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-gray-400">{label}</span>
        {icon}
      </div>
      <div className="text-2xl font-bold text-white mb-0.5">{value}</div>
      <div className="text-xs text-gray-400">{sub}</div>
    </div>
  )
}
