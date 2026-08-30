/**
 * SkillGapPage — The central product statement page.
 * Shows the full deterministic skill gap analysis:
 *   Required skills → current mastery → gap → status → priority order
 * Every number comes from the DB mastery table, not the LLM.
 */
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Target, Loader2, RefreshCw, Info, ChevronRight, AlertTriangle, Lightbulb, GitBranch, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import type { SkillGapReport, SkillGapItem, SkillExplanation } from '@/types'

const STATUS_CONFIG = {
  strong:     { label: 'Strong',      bar: 'bg-emerald-500', badge: 'badge-strong',     text: 'text-emerald-400', icon: '✅' },
  developing: { label: 'Developing',  bar: 'bg-amber-500',   badge: 'badge-developing', text: 'text-amber-400',   icon: '🔶' },
  gap:        { label: 'Gap',         bar: 'bg-rose-500',    badge: 'badge-gap',        text: 'text-rose-400',    icon: '🔴' },
}

function SkeletonBar() {
  return (
    <div className="animate-pulse space-y-2">
      <div className="flex justify-between">
        <div className="h-4 bg-white/10 rounded w-32" />
        <div className="h-4 bg-white/10 rounded w-10" />
      </div>
      <div className="h-2 bg-white/10 rounded-full w-full" />
    </div>
  )
}

export default function SkillGapPage() {
  const { profile, isProfileLoading } = useAuthStore()
  const qc = useQueryClient()
  const [explainSkill, setExplainSkill] = useState<string | null>(null)
  const [prereqOpen, setPrereqOpen] = useState<string | null>(null)

  // Sync customRole when profile loads (profile was null on initial render)
  const [customRole, setCustomRole] = useState('')
  useEffect(() => {
    if (profile?.career_goal && !customRole) {
      setCustomRole(profile.career_goal)
    }
  }, [profile?.career_goal])

  // Deterministic GET — reads from SkillMastery table
  // enabled: wait for profile to finish loading, then check career_goal
  const { data: gapData, isLoading, refetch } = useQuery<SkillGapReport>({
    queryKey: ['skill-gap-current'],
    queryFn: () => api.get('/analytics/skill-gap').then(r => r.data),
    enabled: !isProfileLoading && !!profile?.career_goal,
    retry: false,
  })

  // Skill explanation (on-demand, AI-grounded in real mastery numbers)
  const { data: explanation, isLoading: explainLoading } = useQuery<SkillExplanation>({
    queryKey: ['skill-explain', explainSkill],
    queryFn: () => api.get(`/analytics/explain/${encodeURIComponent(explainSkill!)}`).then(r => r.data),
    enabled: !!explainSkill,
  })

  // Manual re-analysis with custom role
  const reanalyzeMutation = useMutation({
    mutationFn: () => api.post('/analytics/skill-gap', {
      current_skills: profile?.current_skills ?? [],
      target_role: customRole,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['skill-gap-current'] })
      toast.success('Skill gap updated!')
    },
    onError: () => toast.error('Analysis failed — check your profile has a career goal'),
  })

  const readinessPct = gapData?.career_readiness_pct ?? 0
  const readinessColor = readinessPct >= 70 ? 'text-emerald-400' : readinessPct >= 40 ? 'text-amber-400' : 'text-rose-400'

  // Determine what to show
  const showSkeleton = isProfileLoading || (!!profile?.career_goal && isLoading)
  const showNoGoalCTA = !isProfileLoading && !!profile && !profile.career_goal

  return (
    <div className="max-w-4xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Target className="w-6 h-6 text-rose-400" /> Skill Gap Analysis
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Deterministic — scores from your assessment history, not AI guesses
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={customRole}
            onChange={e => setCustomRole(e.target.value)}
            placeholder="Target role…"
            className="input-field py-2 text-sm w-44"
            aria-label="Target role for skill gap analysis"
          />
          <button
            onClick={() => reanalyzeMutation.mutate()}
            disabled={reanalyzeMutation.isPending || !customRole}
            className="btn-secondary py-2 flex items-center gap-1.5 text-sm"
            aria-label="Run skill gap analysis"
          >
            {reanalyzeMutation.isPending
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <RefreshCw className="w-3.5 h-3.5" />}
            Analyze
          </button>
        </div>
      </div>

      {/* Skeleton loading state */}
      {showSkeleton && (
        <div className="glass-card p-6 space-y-4">
          <div className="animate-pulse h-6 bg-white/10 rounded w-48 mb-4" />
          {[...Array(5)].map((_, i) => <SkeletonBar key={i} />)}
        </div>
      )}

      {/* No profile at all — complete onboarding first */}
      {!isProfileLoading && !profile && (
        <div className="glass-card p-10 text-center">
          <Target className="w-12 h-12 text-rose-400/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Complete onboarding first</h3>
          <p className="text-gray-400 text-sm mb-6">
            Set up your profile to get a personalized skill gap analysis.
          </p>
          <Link to="/onboarding" className="btn-primary inline-flex items-center gap-2">
            Start Onboarding <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}

      {/* Profile exists but no career goal */}
      {showNoGoalCTA && (
        <div className="glass-card p-10 text-center">
          <Target className="w-12 h-12 text-rose-400/50 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Set your career goal to see your skill gap</h3>
          <p className="text-gray-400 text-sm mb-6">
            We'll analyze exactly which skills you need and how far you are from each one.
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <Link to="/dashboard/profile" className="btn-primary inline-flex items-center gap-2">
              Set Career Goal <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={() => reanalyzeMutation.mutate()}
              disabled={!customRole || reanalyzeMutation.isPending}
              className="btn-secondary inline-flex items-center gap-2"
            >
              {reanalyzeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
              Analyze Custom Role
            </button>
          </div>
        </div>
      )}

      {/* Main gap data */}
      {gapData && !showSkeleton && (
        <>
          {/* Career Readiness Summary */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between flex-wrap gap-6">
              {/* Gauge */}
              <div className="flex items-center gap-5">
                <div className="relative w-20 h-20">
                  <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="10" />
                    <circle cx="50" cy="50" r="40" fill="none" stroke="url(#cgGrad)" strokeWidth="10"
                      strokeDasharray={`${(readinessPct / 100) * 251.2} 251.2`} strokeLinecap="round" />
                    <defs>
                      <linearGradient id="cgGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#6366f1" /><stop offset="100%" stopColor="#a855f7" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className={`text-xl font-bold ${readinessColor}`}>{Math.round(readinessPct)}</span>
                    <span className="text-xs text-gray-500">/ 100</span>
                  </div>
                </div>
                <div>
                  <p className="text-xl font-bold text-white">{gapData.target_role}</p>
                  <p className={`font-semibold ${readinessColor}`}>
                    {readinessPct >= 70 ? '✅ Interview Ready' : readinessPct >= 40 ? '📚 Developing' : '🚀 Getting Started'}
                  </p>
                  <p className="text-sm text-gray-400 mt-0.5">Career Readiness Score</p>
                </div>
              </div>

              {/* Quick stats */}
              <div className="flex gap-4">
                <div className="text-center px-4 py-2 rounded-xl" style={{ background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.2)' }}>
                  <div className="text-2xl font-bold text-emerald-400">{gapData.strong_skills.length}</div>
                  <div className="text-xs text-emerald-300 mt-0.5">Strong</div>
                </div>
                <div className="text-center px-4 py-2 rounded-xl" style={{ background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.2)' }}>
                  <div className="text-2xl font-bold text-amber-400">{gapData.developing_skills.length}</div>
                  <div className="text-xs text-amber-300 mt-0.5">Developing</div>
                </div>
                <div className="text-center px-4 py-2 rounded-xl" style={{ background: 'rgba(244,63,94,0.1)', border: '1px solid rgba(244,63,94,0.2)' }}>
                  <div className="text-2xl font-bold text-rose-400">{gapData.gap_skills.length}</div>
                  <div className="text-xs text-rose-300 mt-0.5">Gaps</div>
                </div>
              </div>
            </div>
          </div>

          {/* Priority order */}
          {gapData.priority_skills.length > 0 && (
            <div className="glass-card p-5">
              <p className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <ChevronRight className="w-4 h-4 text-indigo-400" />
                Priority Learning Order
                <span className="text-xs text-gray-500 font-normal">(gap × importance, descending)</span>
              </p>
              <div className="flex flex-wrap gap-2">
                {gapData.priority_skills.map((skill, i) => (
                  <button
                    key={skill}
                    onClick={() => setExplainSkill(explainSkill === skill ? null : skill)}
                    aria-label={`Why learn ${skill}? (priority #${i + 1})`}
                    className="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm border transition-all"
                    style={{
                      background: explainSkill === skill ? 'rgba(99,102,241,0.2)' : 'rgba(255,255,255,0.04)',
                      borderColor: explainSkill === skill ? 'rgba(99,102,241,0.5)' : 'rgba(255,255,255,0.1)',
                    }}
                  >
                    <span className="text-indigo-400 font-bold text-xs">#{i + 1}</span>
                    <span className="text-gray-300">{skill}</span>
                    <Info className="w-3 h-3 text-gray-600" />
                  </button>
                ))}
              </div>

              {/* Explanation panel */}
              <AnimatePresence>
                {explainSkill && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-3 p-4 rounded-xl" style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)' }}>
                      {explainLoading ? (
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                          <Loader2 className="w-4 h-4 animate-spin" /> Generating grounded explanation…
                        </div>
                      ) : explanation ? (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0" />
                            <p className="text-sm font-semibold text-white">Why <span className="text-indigo-300">{explainSkill}</span>?</p>
                            <span className="text-xs text-gray-500 ml-auto">Mastery: {explanation.current_mastery}%</span>
                          </div>
                          <p className="text-sm text-gray-300 leading-relaxed">{explanation.explanation}</p>
                          {explanation.prerequisites.length > 0 && (
                            <div className="mt-2 flex items-center gap-2">
                              <GitBranch className="w-3.5 h-3.5 text-gray-500" />
                              <span className="text-xs text-gray-500">Prerequisites:</span>
                              <span className="text-xs text-gray-400">{explanation.prerequisites.join(' → ')}</span>
                            </div>
                          )}
                        </div>
                      ) : null}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Per-skill mastery bars */}
          <div className="glass-card p-6">
            <h2 className="font-semibold text-white mb-5 flex items-center gap-2">
              <Target className="w-4 h-4 text-rose-400" />
              Per-Skill Mastery
              <span className="text-xs text-gray-500 font-normal ml-1">green ≥70% · amber 35–69% · red &lt;35%</span>
            </h2>
            <div className="space-y-4">
              {gapData.required_skills?.map((item: SkillGapItem) => {
                const cfg = STATUS_CONFIG[item.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.gap
                return (
                  <div key={item.skill}>
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-white">{cfg.icon} {item.skill}</span>
                        <span className={`${cfg.badge}`}>{cfg.label}</span>
                        {!item.prerequisites_met && (
                          <span className="text-xs px-1.5 py-0.5 rounded-full text-orange-300"
                            style={{ background: 'rgba(249,115,22,0.15)', border: '1px solid rgba(249,115,22,0.25)' }}
                            title={`Prerequisite gap: ${item.prerequisites.join(', ')}`}>
                            prereq needed
                          </span>
                        )}
                        <button
                          onClick={() => setExplainSkill(item.skill === explainSkill ? null : item.skill)}
                          aria-label={`Explain why ${item.skill} is recommended`}
                          title={`Why ${item.skill}?`}
                          className="text-gray-600 hover:text-indigo-400 transition-colors"
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>Importance: {Math.round(item.importance * 100)}%</span>
                        <span className={`font-semibold ${cfg.text}`}>{Math.round(item.current_mastery)}%</span>
                      </div>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                      <motion.div
                        className={`h-full rounded-full ${cfg.bar}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${item.current_mastery}%` }}
                        transition={{ duration: 0.7, ease: 'easeOut' }}
                      />
                    </div>
                    {/* Prerequisites chain */}
                    {item.prerequisites.length > 0 && (
                      <button
                        onClick={() => setPrereqOpen(prereqOpen === item.skill ? null : item.skill)}
                        aria-label={`Show prerequisites for ${item.skill}`}
                        className="mt-1 text-xs text-gray-600 hover:text-gray-400 flex items-center gap-1"
                      >
                        <GitBranch className="w-3 h-3" />
                        Prerequisites: {item.prerequisites.join(' → ')}
                      </button>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Summary lists */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { title: '✅ Strong Skills', skills: gapData.strong_skills, cls: 'badge-strong', empty: 'Take quizzes to build strong skills' },
              { title: '🔶 Developing', skills: gapData.developing_skills, cls: 'badge-developing', empty: 'Take quizzes to push these to Strong' },
              { title: '🔴 Skill Gaps', skills: gapData.gap_skills, cls: 'badge-gap', empty: 'No critical gaps — great progress!' },
            ].map(section => (
              <div key={section.title} className="glass-card p-5">
                <h3 className="text-sm font-semibold text-white mb-3">{section.title}</h3>
                {section.skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {section.skills.map(s => (
                      <span key={s} className={section.cls}>{s}</span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-500">{section.empty}</p>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
