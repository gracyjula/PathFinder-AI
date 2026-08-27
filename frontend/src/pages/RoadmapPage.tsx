import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2, Circle, ChevronDown, ChevronUp, ExternalLink,
  Plus, Loader2, Lock, Zap, RefreshCw, AlertTriangle, TrendingUp, Info,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import type { Roadmap, AdaptationResult, MilestoneAdaptation, SkillExplanation } from '@/types'

const DIFFICULTY_COLOR = {
  beginner: 'text-green-400 bg-green-400/10',
  intermediate: 'text-yellow-400 bg-yellow-400/10',
  advanced: 'text-red-400 bg-red-400/10',
}

const ADAPTATION_CONFIG = {
  accelerate: { label: '⚡ Can Accelerate', cls: 'bg-green-500/20 text-green-300 border-green-500/30' },
  reinforce: { label: '🔁 Needs Reinforcement', cls: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30' },
  normal: { label: '✅ On Track', cls: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
}

export default function RoadmapPage() {
  const [expandedMilestone, setExpandedMilestone] = useState<string | null>(null)
  const [generatingGoal, setGeneratingGoal] = useState('')
  const [adaptationData, setAdaptationData] = useState<AdaptationResult | null>(null)
  const [explainSkill, setExplainSkill] = useState<string | null>(null)
  const qc = useQueryClient()

  const { data: roadmaps, isLoading } = useQuery<Roadmap[]>({
    queryKey: ['roadmaps'],
    queryFn: () => api.get('/roadmap').then(r => r.data),
  })

  const activeRoadmap = roadmaps?.find(r => r.status === 'active') || roadmaps?.[0]

  const completeMutation = useMutation({
    mutationFn: ({ roadmapId, milestoneId }: { roadmapId: string; milestoneId: string }) =>
      api.patch(`/roadmap/${roadmapId}/milestone/${milestoneId}/complete`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['roadmaps'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      qc.invalidateQueries({ queryKey: ['next-best-action'] })
      toast.success('Milestone completed! 🎉')
    },
    onError: () => toast.error('Failed to complete milestone'),
  })

  const generateMutation = useMutation({
    mutationFn: (goal: string) => api.post('/roadmap', { goal, target_timeline_months: 12 }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['roadmaps'] })
      toast.success('Roadmap generated!')
    },
    onError: () => toast.error('Failed to generate roadmap'),
  })

  const adaptMutation = useMutation({
    mutationFn: (roadmapId: string) => api.post(`/roadmap/${roadmapId}/adapt`),
    onSuccess: (res) => {
      setAdaptationData(res.data)
      qc.invalidateQueries({ queryKey: ['roadmaps'] })
      qc.invalidateQueries({ queryKey: ['next-best-action'] })
      toast.success(`Roadmap adapted — ${res.data.summary}`)
    },
    onError: () => toast.error('Adaptation failed'),
  })

  // On-demand skill explanation
  const { data: explanation, isLoading: explainLoading } = useQuery<SkillExplanation>({
    queryKey: ['skill-explain', explainSkill],
    queryFn: () => api.get(`/analytics/explain/${encodeURIComponent(explainSkill!)}`).then(r => r.data),
    enabled: !!explainSkill,
  })

  // Build adaptation lookup map: milestone_id → MilestoneAdaptation
  const adaptMap = new Map<string, MilestoneAdaptation>(
    adaptationData?.adaptations.map(a => [a.milestone_id, a]) ?? []
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
      </div>
    )
  }

  if (!activeRoadmap) {
    return (
      <div className="max-w-2xl mx-auto text-center py-20">
        <div className="w-16 h-16 rounded-full bg-primary-500/10 flex items-center justify-center mx-auto mb-4">
          <Plus className="w-8 h-8 text-primary-400" />
        </div>
        <h2 className="text-2xl font-bold mb-3">No roadmap yet</h2>
        <p className="text-gray-400 mb-6">Generate a personalized roadmap by chatting with your AI mentor or enter a goal below.</p>
        <div className="flex gap-3 max-w-md mx-auto">
          <input value={generatingGoal} onChange={e => setGeneratingGoal(e.target.value)}
            placeholder="e.g. Become an AI Engineer" className="input-field flex-1" />
          <button
            onClick={() => generateMutation.mutate(generatingGoal)}
            disabled={!generatingGoal || generateMutation.isPending}
            className="btn-primary whitespace-nowrap"
          >
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Generate'}
          </button>
        </div>
      </div>
    )
  }

  const completedCount = activeRoadmap.milestones.filter(m => m.is_completed).length

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white mb-1">{activeRoadmap.title}</h1>
            <p className="text-gray-400 text-sm">{activeRoadmap.description}</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="glass-card px-4 py-3 text-center min-w-[100px]">
              <div className="text-2xl font-bold gradient-text">{activeRoadmap.completion_percentage}%</div>
              <div className="text-xs text-gray-400">Complete</div>
            </div>
            {/* Adapt Roadmap button */}
            <button
              onClick={() => adaptMutation.mutate(activeRoadmap.id)}
              disabled={adaptMutation.isPending}
              className="btn-secondary flex items-center gap-2 py-2.5"
              title="Re-analyze your roadmap based on current skill mastery"
            >
              {adaptMutation.isPending
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <RefreshCw className="w-4 h-4" />
              }
              <span className="hidden sm:inline">Adapt Roadmap</span>
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4 bg-white/5 rounded-full h-2 overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${activeRoadmap.completion_percentage}%` }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </div>
        <div className="flex justify-between text-xs text-gray-500 mt-1">
          <span>{completedCount} of {activeRoadmap.milestones.length} milestones</span>
          <span>{activeRoadmap.total_months} month roadmap</span>
        </div>

        {/* Adaptation summary banner */}
        {adaptationData && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 p-4 rounded-xl bg-gradient-to-r from-primary-500/10 to-accent-500/10 border border-primary-500/20"
          >
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-primary-400" />
              <p className="text-sm font-semibold text-white">Roadmap Adapted</p>
              <span className="text-xs text-gray-400">Career readiness: {Math.round(adaptationData.career_readiness_pct)}%</span>
            </div>
            <p className="text-xs text-gray-300">{adaptationData.summary}</p>
          </motion.div>
        )}
      </div>

      {/* Skill explanation panel */}
      <AnimatePresence>
        {explainSkill && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden mb-4"
          >
            <div className="glass-card p-4 border border-accent-500/20">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-start gap-2 flex-1">
                  <Info className="w-4 h-4 text-accent-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-semibold text-white mb-1">Why <span className="gradient-text">{explainSkill}</span>?</p>
                    {explainLoading ? (
                      <div className="flex items-center gap-2 text-xs text-gray-400">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Generating explanation…
                      </div>
                    ) : (
                      <p className="text-sm text-gray-300 leading-relaxed">{explanation?.explanation}</p>
                    )}
                    {explanation && (
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span>Mastery: <span className="text-gray-300">{explanation.current_mastery}%</span></span>
                        {explanation.prerequisites.length > 0 && (
                          <span>Prerequisites: <span className="text-gray-300">{explanation.prerequisites.join(', ')}</span></span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <button onClick={() => setExplainSkill(null)} className="text-gray-500 hover:text-gray-300 text-xs">✕</button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Timeline */}
      <div className="relative">
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-white/5 hidden md:block" />

        <div className="space-y-4">
          {activeRoadmap.milestones.map((milestone, idx) => {
            const isExpanded = expandedMilestone === milestone.id
            const isUnlocked = idx === 0 || activeRoadmap.milestones[idx - 1]?.is_completed
            const canComplete = isUnlocked && !milestone.is_completed
            const adapt = adaptMap.get(milestone.id)
            const adaptCfg = adapt ? ADAPTATION_CONFIG[adapt.adaptation_status] : null

            return (
              <motion.div
                key={milestone.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.04 }}
                className={`relative md:pl-14 ${!isUnlocked ? 'opacity-60' : ''}`}
              >
                {/* Timeline dot */}
                <div className={`absolute left-2.5 w-5 h-5 rounded-full border-2 items-center justify-center hidden md:flex z-10 bg-[#0a0a1a] ${
                  milestone.is_completed ? 'border-green-500' : isUnlocked ? 'border-primary-500' : 'border-white/20'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${milestone.is_completed ? 'bg-green-500' : isUnlocked ? 'bg-primary-500' : 'bg-white/20'}`} />
                </div>

                <div className={`milestone-card ${isExpanded ? 'border-primary-500/40' : ''} ${adapt?.adaptation_status === 'reinforce' ? 'border-yellow-500/20' : adapt?.adaptation_status === 'accelerate' ? 'border-green-500/20' : ''}`}>
                  {/* Milestone header */}
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => setExpandedMilestone(isExpanded ? null : milestone.id)}
                  >
                    <div className="flex items-start gap-3 flex-1">
                      <button
                        onClick={e => {
                          e.stopPropagation()
                          if (canComplete) completeMutation.mutate({ roadmapId: activeRoadmap.id, milestoneId: milestone.id })
                        }}
                        disabled={!canComplete}
                        className="mt-0.5 flex-shrink-0"
                      >
                        {milestone.is_completed
                          ? <CheckCircle2 className="w-5 h-5 text-green-400" />
                          : isUnlocked
                          ? <Circle className="w-5 h-5 text-primary-400 hover:text-primary-300" />
                          : <Lock className="w-5 h-5 text-gray-600" />
                        }
                      </button>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs text-gray-500 font-mono">Month {milestone.month_number}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${DIFFICULTY_COLOR[milestone.difficulty as keyof typeof DIFFICULTY_COLOR] || 'text-gray-400 bg-gray-400/10'}`}>
                            {milestone.difficulty}
                          </span>
                          {milestone.estimated_hours && (
                            <span className="text-xs text-gray-500">~{milestone.estimated_hours}h</span>
                          )}
                          {/* Adaptation badge */}
                          {adaptCfg && (
                            <span className={`text-xs px-2 py-0.5 rounded-full border ${adaptCfg.cls}`}>
                              {adaptCfg.label}
                            </span>
                          )}
                        </div>
                        <h3 className={`font-semibold mt-1 ${milestone.is_completed ? 'text-green-400 line-through' : 'text-white'}`}>
                          {milestone.title}
                        </h3>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {milestone.topics.slice(0, 4).map(t => (
                            <button
                              key={t}
                              onClick={e => { e.stopPropagation(); setExplainSkill(t) }}
                              className="text-xs px-2 py-0.5 rounded-md bg-white/5 text-gray-300 hover:bg-primary-500/20 hover:text-primary-300 transition-colors"
                            >
                              {t}
                            </button>
                          ))}
                          {milestone.topics.length > 4 && (
                            <span className="text-xs text-gray-500">+{milestone.topics.length - 4} more</span>
                          )}
                        </div>
                      </div>
                    </div>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
                  </div>

                  {/* Expanded content */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden"
                      >
                        <div className="pt-4 mt-4 border-t border-white/10 space-y-4">
                          {milestone.description && (
                            <p className="text-gray-400 text-sm">{milestone.description}</p>
                          )}

                          {/* Adaptation details for this milestone */}
                          {adapt && adapt.skill_adaptations.length > 0 && (
                            <div className="rounded-xl bg-white/5 p-3 space-y-2">
                              <p className="text-xs font-semibold text-gray-300 flex items-center gap-1.5">
                                <TrendingUp className="w-3.5 h-3.5 text-primary-400" /> Adaptation Details
                              </p>
                              {adapt.skill_adaptations.map((sa, i) => (
                                <div key={i} className="flex items-start gap-2 text-xs">
                                  <span className={`px-1.5 py-0.5 rounded ${
                                    sa.action === 'accelerate' ? 'bg-green-500/20 text-green-300' :
                                    sa.action === 'reinforce' ? 'bg-yellow-500/20 text-yellow-300' :
                                    'bg-blue-500/20 text-blue-300'
                                  }`}>{sa.skill}</span>
                                  <span className="text-gray-400">{sa.reason}</span>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Resources */}
                          {milestone.resources.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">Resources</h4>
                              <div className="space-y-2">
                                {milestone.resources.map((r, ri) => (
                                  <div key={ri} className="flex items-start justify-between bg-white/5 rounded-xl p-3 gap-3">
                                    <div className="flex-1">
                                      <div className="flex items-center gap-2 mb-1">
                                        <span className="text-xs px-1.5 py-0.5 rounded bg-primary-500/20 text-primary-300">{r.type}</span>
                                        {r.is_free && <span className="text-xs text-green-400">Free</span>}
                                        {r.provider && <span className="text-xs text-gray-500">{r.provider}</span>}
                                      </div>
                                      <p className="text-sm font-medium text-white">{r.title}</p>
                                      {r.why_recommended && (
                                        <p className="text-xs text-gray-400 mt-1 flex items-start gap-1">
                                          <span className="text-yellow-400 flex-shrink-0">💡</span>
                                          {r.why_recommended}
                                        </p>
                                      )}
                                    </div>
                                    {r.url && (
                                      <a href={r.url} target="_blank" rel="noopener noreferrer"
                                        className="text-primary-400 hover:text-primary-300 flex-shrink-0">
                                        <ExternalLink className="w-4 h-4" />
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Projects */}
                          {milestone.projects.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">Projects</h4>
                              <div className="space-y-2">
                                {milestone.projects.map((p, pi) => (
                                  <div key={pi} className="bg-white/5 rounded-xl p-3">
                                    <p className="text-sm font-medium text-white mb-1">{p.title}</p>
                                    <p className="text-xs text-gray-400">{p.description}</p>
                                    <div className="flex flex-wrap gap-1 mt-2">
                                      {p.skills_practiced?.map(s => (
                                        <span key={s} className="text-xs px-1.5 py-0.5 rounded bg-accent-500/10 text-accent-300">{s}</span>
                                      ))}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Outcomes */}
                          {milestone.outcomes.length > 0 && (
                            <div>
                              <h4 className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">Outcomes</h4>
                              <ul className="space-y-1">
                                {milestone.outcomes.map((o, oi) => (
                                  <li key={oi} className="text-sm text-gray-400 flex items-start gap-2">
                                    <span className="text-primary-400 mt-0.5">✓</span> {o}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {canComplete && (
                            <button
                              onClick={() => completeMutation.mutate({ roadmapId: activeRoadmap.id, milestoneId: milestone.id })}
                              disabled={completeMutation.isPending}
                              className="btn-primary w-full flex items-center justify-center gap-2"
                            >
                              {completeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                              Mark as Complete
                            </button>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
