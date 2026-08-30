import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, Tooltip, Cell,
} from 'recharts'
import { Brain, Target, TrendingUp, Calendar, Loader2, RefreshCw, Lightbulb, ChevronRight, Info } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { SkillGapReport, SkillGapItem, SkillExplanation } from '@/types'

const STATUS_COLOR: Record<string, string> = {
  strong: 'bg-green-500',
  developing: 'bg-yellow-500',
  gap: 'bg-red-500',
}
const STATUS_LABEL: Record<string, string> = {
  strong: 'Strong',
  developing: 'Developing',
  gap: 'Gap',
}

export default function AnalyticsPage() {
  const { profile, isProfileLoading } = useAuthStore()
  const qc = useQueryClient()
  const [gapRole, setGapRole] = useState(profile?.career_goal || '')
  const [explainSkill, setExplainSkill] = useState<string | null>(null)

  // Sync gapRole when profile loads (profile may be null on initial render)
  useEffect(() => {
    if (profile?.career_goal && !gapRole) {
      setGapRole(profile.career_goal)
    }
  }, [profile?.career_goal]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Deterministic skill gap from mastery data ──────────────────────────────
  const { data: gapData, isLoading: gapLoading, refetch: refetchGap } = useQuery<SkillGapReport>({
    queryKey: ['skill-gap-current'],
    queryFn: () => api.get('/analytics/skill-gap').then(r => r.data),
    // Wait for profile to load before checking career_goal
    enabled: !isProfileLoading && !!profile?.career_goal,
    retry: false,
  })

  // Manual gap analysis (POST with different role)
  const gapMutation = useMutation({
    mutationFn: () => api.post('/analytics/skill-gap', {
      current_skills: profile?.current_skills ?? [],
      target_role: gapRole,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['skill-gap-current'] })
      toast.success('Skill gap analysis updated!')
    },
    onError: () => toast.error('Analysis failed'),
  })

  // Career readiness
  const { data: readiness, isLoading: rLoading, refetch: refetchReadiness } = useQuery({
    queryKey: ['career-readiness'],
    queryFn: () => api.get('/analytics/career-readiness').then(r => r.data),
    retry: false,
  })

  // Weekly plan
  const { data: weeklyPlan, isLoading: wpLoading } = useQuery({
    queryKey: ['weekly-plan'],
    queryFn: () => api.get('/analytics/weekly-plan').then(r => r.data),
    retry: false,
  })

  // Skill explanation (on-demand)
  const { data: explanation, isLoading: explainLoading } = useQuery<SkillExplanation>({
    queryKey: ['skill-explain', explainSkill],
    queryFn: () => api.get(`/analytics/explain/${encodeURIComponent(explainSkill!)}`).then(r => r.data),
    enabled: !!explainSkill,
  })

  const activeGap: SkillGapReport | undefined = gapMutation.data?.data ?? gapData

  // Radar: all required skills with current mastery
  const radarData = activeGap?.required_skills
    ?.slice(0, 8)
    .map((item: SkillGapItem) => ({
      name: item.skill.length > 12 ? item.skill.slice(0, 11) + '…' : item.skill,
      value: Math.round(item.current_mastery),
    })) ?? []

  const breakdownData = readiness?.breakdown
    ? Object.entries(readiness.breakdown).map(([name, value]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1),
        value: value as number,
      }))
    : []

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Analytics & Insights</h1>

      {/* ── Skill Gap (deterministic) ──────────────────────────────────────── */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
          <h2 className="font-semibold text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-accent-400" /> Skill Gap Analysis
            <span className="text-xs text-gray-500 font-normal">(deterministic, real-time)</span>
          </h2>
          <div className="flex gap-2">
            <input
              value={gapRole}
              onChange={e => setGapRole(e.target.value)}
              placeholder="Target role…"
              className="input-field py-1.5 text-sm w-44"
            />
            <button
              onClick={() => gapMutation.mutate()}
              disabled={gapMutation.isPending || !gapRole}
              className="btn-secondary py-1.5 flex items-center gap-1.5 text-sm"
            >
              {gapMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
              Analyze
            </button>
          </div>
        </div>

        {gapLoading ? (
          <div className="flex items-center justify-center h-32"><Loader2 className="w-6 h-6 animate-spin text-primary-400" /></div>
        ) : activeGap ? (
          <div className="space-y-6">
            {/* Summary row */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <div className="text-3xl font-bold text-primary-400">{Math.round(activeGap.career_readiness_pct)}%</div>
                <div className="text-xs text-gray-400 mt-1">Career Readiness</div>
              </div>
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <div className="text-3xl font-bold text-green-400">{activeGap.strong_skills.length}</div>
                <div className="text-xs text-gray-400 mt-1">Strong Skills</div>
              </div>
              <div className="bg-white/5 rounded-xl p-4 text-center">
                <div className="text-3xl font-bold text-red-400">{activeGap.gap_skills.length}</div>
                <div className="text-xs text-gray-400 mt-1">Skill Gaps</div>
              </div>
            </div>

            {/* Skill bars + radar */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Skill mastery bars */}
              <div className="space-y-2.5">
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Per-Skill Mastery</p>
                {activeGap.required_skills?.map((item: SkillGapItem) => (
                  <div key={item.skill}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-300">{item.skill}</span>
                        <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                          item.status === 'strong' ? 'bg-green-500/20 text-green-300' :
                          item.status === 'developing' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-red-500/20 text-red-300'
                        }`}>
                          {STATUS_LABEL[item.status]}
                        </span>
                        <button
                          onClick={() => setExplainSkill(explainSkill === item.skill ? null : item.skill)}
                          className="text-gray-600 hover:text-primary-400 transition-colors"
                          title="Why this skill?"
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <span className="text-xs text-gray-500">{Math.round(item.current_mastery)}%</span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${STATUS_COLOR[item.status]}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${item.current_mastery}%` }}
                        transition={{ duration: 0.6 }}
                      />
                    </div>
                    {/* Inline explanation */}
                    <AnimatePresence>
                      {explainSkill === item.skill && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-2 p-3 bg-primary-500/10 rounded-lg border border-primary-500/20">
                            {explainLoading ? (
                              <div className="flex items-center gap-2 text-xs text-gray-400">
                                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Generating explanation…
                              </div>
                            ) : explanation?.explanation ? (
                              <p className="text-xs text-gray-300 leading-relaxed">
                                <Lightbulb className="w-3.5 h-3.5 text-yellow-400 inline mr-1.5 -mt-0.5" />
                                {explanation.explanation}
                              </p>
                            ) : null}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))}
              </div>

              {/* Radar chart */}
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-3">Skill Coverage</p>
                {radarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={220}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                      <Radar name="Mastery" dataKey="value" stroke="#cc33f0" fill="#cc33f0" fillOpacity={0.2} />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-44 text-gray-500 text-sm">
                    No data yet
                  </div>
                )}
              </div>
            </div>

            {/* Priority skills */}
            {activeGap.priority_skills.length > 0 && (
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Priority Learning Order</p>
                <div className="flex flex-wrap gap-2">
                  {activeGap.priority_skills.map((s, i) => (
                    <div key={s} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                      <span className="text-xs font-bold text-primary-400">#{i + 1}</span>
                      <span className="text-sm text-gray-300">{s}</span>
                      <button
                        onClick={() => setExplainSkill(s)}
                        className="text-gray-600 hover:text-primary-400 transition-colors"
                      >
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-400 text-sm">Complete your profile with a career goal to see your skill gap.</p>
        )}
      </div>

      {/* ── Career Readiness ──────────────────────────────────────────────── */}
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
                  {!readiness.interview_ready && readiness.estimated_months_to_ready && (
                    <p className="text-sm text-gray-400 mt-1">{readiness.estimated_months_to_ready} months to ready</p>
                  )}
                </div>
              </div>
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

      {/* ── Weekly Plan ───────────────────────────────────────────────────── */}
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
