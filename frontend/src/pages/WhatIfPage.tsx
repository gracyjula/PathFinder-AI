import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Zap, TrendingUp, TrendingDown, Minus, Loader2, RefreshCw, AlertTriangle } from 'lucide-react'
import { motion } from 'framer-motion'
import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer, Legend,
} from 'recharts'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { WhatIfResult } from '@/types'

const ROLES = [
  'AI Engineer', 'ML Engineer', 'Data Scientist', 'Generative AI Engineer',
  'Full Stack Developer', 'Cloud Engineer', 'Software Engineer', 'Data Analyst',
]

export default function WhatIfPage() {
  const { profile } = useAuthStore()

  const [weeklyHours, setWeeklyHours] = useState(profile?.weekly_hours ?? 10)
  const [targetRole, setTargetRole] = useState(profile?.career_goal ?? 'AI Engineer')
  const [timelineMonths, setTimelineMonths] = useState(profile?.target_timeline_months ?? 12)
  const [knownSkills, setKnownSkills] = useState('')

  const queryKey = ['whatif', weeklyHours, targetRole, timelineMonths, knownSkills]

  const { data, isLoading, refetch, isFetching } = useQuery<WhatIfResult>({
    queryKey,
    queryFn: () => {
      const params = new URLSearchParams({
        weekly_hours: String(weeklyHours),
        target_role: targetRole,
        timeline_months: String(timelineMonths),
        ...(knownSkills ? { known_skills: knownSkills } : {}),
      })
      return api.post(`/analytics/whatif?${params.toString()}`).then(r => r.data)
    },
    enabled: false,   // manual trigger only
    retry: false,
  })

  const canRun = !!targetRole

  // Radar comparison data
  const radarData = data
    ? data.current.priority_skills.slice(0, 6).map(skill => ({
        skill,
        current: 0,   // we don't have per-skill mastery here, use readiness as proxy
        simulated: 0,
      }))
    : []

  const delta = data?.impact.readiness_change ?? 0
  const monthsDelta = data?.impact.months_change ?? 0
  const DeltaIcon = delta > 0 ? TrendingUp : delta < 0 ? TrendingDown : Minus
  const deltaColor = delta > 0 ? 'text-green-400' : delta < 0 ? 'text-red-400' : 'text-gray-400'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2 mb-1">
          <Zap className="w-6 h-6 text-accent-400" /> What-If Simulator
        </h1>
        <p className="text-gray-400 text-sm">
          Simulate how your learning path would change under different parameters — without affecting your actual roadmap.
        </p>
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* ── Controls ───────────────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-5">
          <div className="glass-card p-5 space-y-5">
            <h2 className="font-semibold text-white text-sm uppercase tracking-wide">Simulation Parameters</h2>

            {/* Target Role */}
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block">Target Role</label>
              <select
                value={targetRole}
                onChange={e => setTargetRole(e.target.value)}
                className="input-field text-sm"
              >
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>

            {/* Weekly hours slider */}
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block">
                Weekly Study Hours: <span className="text-white font-semibold">{weeklyHours}h</span>
              </label>
              <input
                type="range" min={1} max={40} step={1}
                value={weeklyHours}
                onChange={e => setWeeklyHours(Number(e.target.value))}
                className="w-full accent-primary-500"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>1h</span><span>20h</span><span>40h</span>
              </div>
            </div>

            {/* Timeline slider */}
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block">
                Target Timeline: <span className="text-white font-semibold">{timelineMonths} months</span>
              </label>
              <input
                type="range" min={3} max={24} step={1}
                value={timelineMonths}
                onChange={e => setTimelineMonths(Number(e.target.value))}
                className="w-full accent-primary-500"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>3mo</span><span>12mo</span><span>24mo</span>
              </div>
            </div>

            {/* Extra known skills */}
            <div>
              <label className="text-xs text-gray-400 mb-1.5 block">
                "I already know…" <span className="text-gray-600">(comma separated)</span>
              </label>
              <input
                value={knownSkills}
                onChange={e => setKnownSkills(e.target.value)}
                placeholder="e.g. Python, Docker"
                className="input-field text-sm"
              />
            </div>

            <button
              onClick={() => refetch()}
              disabled={!canRun || isFetching}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {isFetching
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <RefreshCw className="w-4 h-4" />
              }
              Run Simulation
            </button>
          </div>

          {/* Current state reference */}
          {profile && (
            <div className="glass-card p-4 text-xs text-gray-500 space-y-1">
              <p className="text-gray-400 font-semibold mb-2">Current Settings</p>
              <p>Role: <span className="text-gray-300">{profile.career_goal || 'Not set'}</span></p>
              <p>Hours/week: <span className="text-gray-300">{profile.weekly_hours ?? '—'}</span></p>
              <p>Timeline: <span className="text-gray-300">{profile.target_timeline_months ?? '—'} months</span></p>
            </div>
          )}
        </div>

        {/* ── Results ────────────────────────────────────────────────────── */}
        <div className="lg:col-span-3 space-y-5">
          {isLoading || isFetching ? (
            <div className="glass-card p-12 flex flex-col items-center justify-center gap-3">
              <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
              <p className="text-gray-400 text-sm">Running simulation…</p>
            </div>
          ) : data ? (
            <>
              {/* Simulation label */}
              <div className="glass-card p-4 border border-accent-500/20 bg-accent-500/5">
                <p className="text-xs font-semibold text-accent-400 uppercase tracking-wide mb-1">
                  {data.simulation_label}
                </p>
                {data.changes.map((c, i) => (
                  <p key={i} className="text-sm text-gray-300">• {c}</p>
                ))}
              </div>

              {/* Impact summary */}
              <div className="grid grid-cols-3 gap-3">
                <ImpactCard
                  label="Readiness Change"
                  value={`${delta > 0 ? '+' : ''}${delta.toFixed(1)}%`}
                  sub={`${data.simulated.career_readiness_pct.toFixed(1)}% readiness`}
                  icon={<DeltaIcon className={`w-5 h-5 ${deltaColor}`} />}
                  color={delta > 0 ? 'from-green-500/20 to-green-500/10' : delta < 0 ? 'from-red-500/20 to-red-500/10' : 'from-gray-500/20 to-gray-500/10'}
                />
                <ImpactCard
                  label="Time to Complete"
                  value={`${data.simulated.estimated_months_needed}mo`}
                  sub={monthsDelta !== 0 ? `${monthsDelta > 0 ? '+' : ''}${monthsDelta.toFixed(1)}mo vs current` : 'No change'}
                  icon={<Zap className="w-5 h-5 text-yellow-400" />}
                  color="from-yellow-500/20 to-yellow-500/10"
                />
                <ImpactCard
                  label="Feasible?"
                  value={data.simulated.feasible_in_timeline ? 'Yes ✅' : 'No ⚠️'}
                  sub={`${data.simulated.total_available_hours}h available`}
                  icon={<TrendingUp className={`w-5 h-5 ${data.simulated.feasible_in_timeline ? 'text-green-400' : 'text-red-400'}`} />}
                  color={data.simulated.feasible_in_timeline ? 'from-green-500/20 to-green-500/10' : 'from-red-500/20 to-red-500/10'}
                />
              </div>

              {/* AI explanation */}
              {data.impact.explanation && (
                <div className="glass-card p-4">
                  <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">AI Analysis</p>
                  <p className="text-sm text-gray-300 leading-relaxed">{data.impact.explanation}</p>
                </div>
              )}

              {/* Side-by-side comparison */}
              <div className="glass-card p-5">
                <h3 className="font-semibold text-white text-sm mb-4">Scenario Comparison</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {/* Current */}
                  <div>
                    <p className="text-xs text-gray-500 uppercase mb-2">Current</p>
                    <ComparisonRow label="Role" value={data.current.role} />
                    <ComparisonRow label="Hours/wk" value={`${data.current.weekly_hours}h`} />
                    <ComparisonRow label="Timeline" value={`${data.current.timeline_months}mo`} />
                    <ComparisonRow label="Readiness" value={`${data.current.career_readiness_pct.toFixed(1)}%`} />
                    <ComparisonRow label="Est. months" value={`${data.current.estimated_months_needed}`} />
                    <ComparisonRow label="Gap hours" value={`~${data.current.estimated_gap_hours}h`} />
                  </div>
                  {/* Simulated */}
                  <div>
                    <p className="text-xs text-accent-400 uppercase mb-2">Simulated</p>
                    <ComparisonRow label="Role" value={data.simulated.role} highlight={data.simulated.role !== data.current.role} />
                    <ComparisonRow label="Hours/wk" value={`${data.simulated.weekly_hours}h`} highlight={data.simulated.weekly_hours !== data.current.weekly_hours} />
                    <ComparisonRow label="Timeline" value={`${data.simulated.timeline_months}mo`} highlight={data.simulated.timeline_months !== data.current.timeline_months} />
                    <ComparisonRow label="Readiness" value={`${data.simulated.career_readiness_pct.toFixed(1)}%`} highlight={data.simulated.career_readiness_pct !== data.current.career_readiness_pct} />
                    <ComparisonRow label="Est. months" value={`${data.simulated.estimated_months_needed}`} highlight={data.simulated.estimated_months_needed !== data.current.estimated_months_needed} />
                    <ComparisonRow label="Gap hours" value={`~${data.simulated.estimated_gap_hours}h`} highlight={data.simulated.estimated_gap_hours !== data.current.estimated_gap_hours} />
                  </div>
                </div>

                {/* Priority skills comparison */}
                {(data.simulated.priority_skills.length > 0 || data.current.priority_skills.length > 0) && (
                  <div className="mt-4 pt-4 border-t border-white/10 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 uppercase mb-2">Current Priorities</p>
                      <div className="flex flex-wrap gap-1.5">
                        {data.current.priority_skills.map((s, i) => (
                          <span key={s} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400">
                            #{i + 1} {s}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-accent-400 uppercase mb-2">Simulated Priorities</p>
                      <div className="flex flex-wrap gap-1.5">
                        {data.simulated.priority_skills.map((s, i) => (
                          <span key={s} className={`text-xs px-2 py-0.5 rounded-full ${
                            !data.current.priority_skills.includes(s)
                              ? 'bg-accent-500/20 text-accent-300'
                              : 'bg-white/5 text-gray-400'
                          }`}>
                            #{i + 1} {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {!data.simulated.feasible_in_timeline && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="mt-4 p-3 rounded-xl bg-red-500/10 border border-red-500/20 flex items-start gap-2"
                  >
                    <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-red-300">
                      The simulated timeline may not be sufficient.
                      Estimated {data.simulated.estimated_months_needed} months needed
                      but only {data.simulated.timeline_months} months available.
                      Consider increasing weekly hours or extending the timeline.
                    </p>
                  </motion.div>
                )}
              </div>
            </>
          ) : (
            <div className="glass-card p-12 flex flex-col items-center justify-center gap-3 text-center">
              <Zap className="w-12 h-12 text-gray-700" />
              <p className="text-gray-400 font-medium">Run a simulation to see how changes affect your path</p>
              <p className="text-gray-600 text-sm max-w-xs">
                Adjust the parameters on the left and click "Run Simulation" — nothing will be saved until you confirm.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ImpactCard({ label, value, sub, icon, color }: {
  label: string; value: string; sub: string; icon: React.ReactNode; color: string
}) {
  return (
    <div className={`glass-card p-4 bg-gradient-to-br ${color}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">{label}</span>
        {icon}
      </div>
      <div className="text-xl font-bold text-white">{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{sub}</div>
    </div>
  )
}

function ComparisonRow({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex justify-between py-1 border-b border-white/5">
      <span className="text-gray-500 text-xs">{label}</span>
      <span className={`text-xs font-medium ${highlight ? 'text-accent-300' : 'text-gray-300'}`}>{value}</span>
    </div>
  )
}
