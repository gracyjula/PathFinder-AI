import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts'
import { Brain, Target, TrendingUp, Calendar, Loader2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

export default function AnalyticsPage() {
  const { profile } = useAuthStore()
  const [gapSkills, setGapSkills] = useState(profile?.current_skills?.join(', ') || '')
  const [gapRole, setGapRole] = useState(profile?.career_goal || '')

  const { data: readiness, isLoading: rLoading, refetch: refetchReadiness } = useQuery({
    queryKey: ['career-readiness'],
    queryFn: () => api.get('/analytics/career-readiness').then(r => r.data),
    retry: false,
  })

  const { data: weeklyPlan, isLoading: wpLoading } = useQuery({
    queryKey: ['weekly-plan'],
    queryFn: () => api.get('/analytics/weekly-plan').then(r => r.data),
    retry: false,
  })

  const gapMutation = useMutation({
    mutationFn: () => api.post('/analytics/skill-gap', {
      current_skills: gapSkills.split(',').map(s => s.trim()).filter(Boolean),
      target_role: gapRole,
    }),
    onSuccess: () => toast.success('Skill gap analysis complete!'),
    onError: () => toast.error('Analysis failed'),
  })

  const gapData = gapMutation.data?.data
  const radarData = gapData?.skill_scores
    ? Object.entries(gapData.skill_scores).map(([name, value]) => ({ name, value }))
    : []

  const breakdownData = readiness?.breakdown
    ? Object.entries(readiness.breakdown).map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value: value as number }))
    : []

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Analytics & Insights</h1>

      {/* Career Readiness */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary-400" /> Career Readiness Score
          </h2>
          <button onClick={() => refetchReadiness()} className="btn-secondary py-1.5 flex items-center gap-1.5 text-sm">
            <RefreshCw className="w-3.5 h-3.5" /> Recalculate
          </button>
        </div>

        {rLoading ? (
          <div className="flex items-center justify-center h-32"><Loader2 className="w-6 h-6 animate-spin text-primary-400" /></div>
        ) : readiness ? (
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              {/* Score circle */}
              <div className="flex items-center gap-6 mb-4">
                <div className="relative">
                  <svg viewBox="0 0 100 100" className="w-24 h-24">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
                    <circle cx="50" cy="50" r="40" fill="none" stroke="url(#rGrad)" strokeWidth="8"
                      strokeDasharray={`${(readiness.score / 100) * 251.2} 251.2`}
                      strokeLinecap="round" transform="rotate(-90 50 50)" />
                    <defs>
                      <linearGradient id="rGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#4c6ef5" /><stop offset="100%" stopColor="#cc33f0" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold gradient-text">{readiness.score}</span>
                    <span className="text-xs text-gray-400">/100</span>
                  </div>
                </div>
                <div>
                  <p className={`font-semibold ${readiness.interview_ready ? 'text-green-400' : 'text-yellow-400'}`}>
                    {readiness.interview_ready ? '✅ Interview Ready!' : '📚 Keep Learning'}
                  </p>
                  {!readiness.interview_ready && (
                    <p className="text-sm text-gray-400 mt-1">{readiness.estimated_months_to_ready} months to ready</p>
                  )}
                </div>
              </div>

              {/* Weak/Strong areas */}
              <div className="space-y-3">
                {readiness.strong_areas?.length > 0 && (
                  <div>
                    <p className="text-xs text-green-400 font-medium mb-1.5">✅ Strong Areas</p>
                    <div className="flex flex-wrap gap-1.5">
                      {readiness.strong_areas.map((a: string) => (
                        <span key={a} className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-300">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
                {readiness.weak_areas?.length > 0 && (
                  <div>
                    <p className="text-xs text-red-400 font-medium mb-1.5">⚠️ Weak Areas</p>
                    <div className="flex flex-wrap gap-1.5">
                      {readiness.weak_areas.map((a: string) => (
                        <span key={a} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-300">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Breakdown bar chart */}
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Score Breakdown</p>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={breakdownData} layout="vertical">
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
                  <Tooltip contentStyle={{ background: '#1e1b4b', border: '1px solid #4c6ef5', borderRadius: '8px', color: '#e0e7ff', fontSize: 12 }} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {breakdownData.map((_, i) => (
                      <Cell key={i} fill={`hsl(${220 + i * 20}, 70%, 60%)`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Complete your profile to see career readiness.</p>
        )}

        {readiness?.suggestions && (
          <div className="mt-4 pt-4 border-t border-white/10">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Suggestions</p>
            <ul className="space-y-1">
              {readiness.suggestions.map((s: string, i: number) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-primary-400">→</span> {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Skill Gap Analyzer */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
          <Target className="w-4 h-4 text-accent-400" /> Skill Gap Analyzer
        </h2>
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <input value={gapRole} onChange={e => setGapRole(e.target.value)}
            placeholder="Target Role (e.g. AI Engineer)" className="input-field flex-1" />
          <button onClick={() => gapMutation.mutate()} disabled={gapMutation.isPending || !gapRole}
            className="btn-primary flex items-center gap-2 justify-center sm:w-auto">
            {gapMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
            Analyze Gap
          </button>
        </div>

        {gapData && (
          <div className="grid md:grid-cols-2 gap-6 mt-4">
            <div>
              <div className="flex items-center justify-between mb-3">
                <p className="text-sm font-medium text-white">Gap: <span className="text-red-400">{gapData.gap_percentage?.toFixed(0)}%</span></p>
                <p className="text-xs text-gray-400">{gapData.estimated_months_to_close_gap} months to close</p>
              </div>
              <div className="space-y-2">
                <div>
                  <p className="text-xs text-green-400 mb-1.5">✅ You have</p>
                  <div className="flex flex-wrap gap-1.5">
                    {gapData.current_skills?.map((s: string) => (
                      <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-300">{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-red-400 mb-1.5">❌ Missing</p>
                  <div className="flex flex-wrap gap-1.5">
                    {gapData.missing_skills?.map((s: string) => (
                      <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-300">{s}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.1)" />
                <PolarAngleAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                <Radar name="Skill Level" dataKey="value" stroke="#cc33f0" fill="#cc33f0" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Weekly Plan */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-white mb-4 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-blue-400" /> Weekly Learning Plan
        </h2>
        {wpLoading ? (
          <div className="flex items-center justify-center h-24"><Loader2 className="w-6 h-6 animate-spin text-primary-400" /></div>
        ) : weeklyPlan ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-white font-medium">{weeklyPlan.goal}</p>
              <span className="text-sm text-gray-400">{weeklyPlan.total_hours}h this week</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {weeklyPlan.daily_plans?.slice(0, 6).map((day: any, i: number) => (
                <div key={i} className="bg-white/5 rounded-xl p-3">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium text-white">{day.day}</p>
                    <span className="text-xs text-gray-400">{day.total_minutes}min</span>
                  </div>
                  <ul className="space-y-1.5">
                    {day.tasks?.slice(0, 3).map((task: any, ti: number) => (
                      <li key={ti} className="text-xs text-gray-400 flex items-start gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0 ${
                          task.type === 'study' ? 'bg-blue-400' :
                          task.type === 'practice' ? 'bg-green-400' :
                          task.type === 'project' ? 'bg-purple-400' : 'bg-yellow-400'
                        }`} />
                        {task.title}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Complete your profile to get a weekly plan.</p>
        )}
      </div>
    </div>
  )
}
