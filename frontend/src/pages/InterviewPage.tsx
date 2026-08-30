import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Mic, ChevronDown, ChevronUp, Loader2, Brain, BookOpen,
  CheckCircle2, AlertCircle, ChevronRight,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const ROLES = [
  'AI Engineer', 'Data Scientist', 'Full Stack Developer', 'Backend Developer',
  'ML Engineer', 'Cloud Engineer', 'DevOps Engineer',
]
const DIFFICULTIES = ['easy', 'intermediate', 'hard']
const QUESTION_COUNTS = [3, 5, 8, 10]

type EvalStatus = 'idle' | 'evaluating' | 'done' | 'error'

interface QuestionState {
  expanded: boolean
  userAnswer: string
  evalStatus: EvalStatus
  evalFeedback: string | null
  evalScore: number | null  // 0-100
}

export default function InterviewPage() {
  const { profile } = useAuthStore()
  const [role, setRole] = useState(profile?.career_goal || '')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [numQuestions, setNumQuestions] = useState(5)
  const [interview, setInterview] = useState<any>(null)
  // keyed by "sectionIdx_questionIdx"
  const [qState, setQState] = useState<Record<string, QuestionState>>({})
  const [practiceMode, setPracticeMode] = useState(false)

  // Keep role in sync if profile loads after mount
  useEffect(() => {
    if (profile?.career_goal && !role) {
      setRole(profile.career_goal)
    }
  }, [profile?.career_goal]) // eslint-disable-line react-hooks/exhaustive-deps

  const mutation = useMutation({
    mutationFn: () =>
      api.post(
        `/analytics/mock-interview?role=${encodeURIComponent(role)}&difficulty=${difficulty}`,
      ),
    onSuccess: (res) => {
      setInterview(res.data)
      setQState({})
      setPracticeMode(false)
    },
    onError: () => toast.error('Failed to generate interview questions. Please try again.'),
  })

  const evalMutation = useMutation({
    mutationFn: ({ key, question, userAnswer, sampleAnswer }: {
      key: string; question: string; userAnswer: string; sampleAnswer: string
    }) =>
      api.post('/analytics/quiz/generate', {
        // We reuse the Gemini pipeline via a prompt trick — actual eval happens client-side
        // with deterministic keyword matching as fallback
        topic: `Interview self-eval: ${question.slice(0, 80)}`,
        difficulty: 'intermediate',
        num_questions: 1,
      }).then(() => ({ key, question, userAnswer, sampleAnswer })),
    onSuccess: () => {},
    onError: () => {},
  })

  const getQKey = (si: number, qi: number) => `${si}_${qi}`

  const updateQ = (key: string, patch: Partial<QuestionState>) =>
    setQState(prev => ({ ...prev, [key]: { ...prev[key], ...patch } }))

  const initQ = (key: string) => {
    if (!qState[key]) {
      setQState(prev => ({
        ...prev,
        [key]: { expanded: false, userAnswer: '', evalStatus: 'idle', evalFeedback: null, evalScore: null },
      }))
    }
  }

  const toggleExpand = (key: string) => {
    initQ(key)
    setQState(prev => ({
      ...prev,
      [key]: { ...(prev[key] ?? { userAnswer: '', evalStatus: 'idle', evalFeedback: null, evalScore: null }), expanded: !prev[key]?.expanded },
    }))
  }

  /** Deterministic keyword-based self-evaluation fallback */
  const evaluateAnswer = (userAnswer: string, sampleAnswer: string, expectedTopics: string[]): { score: number; feedback: string } => {
    const lower = userAnswer.toLowerCase()
    const hits = expectedTopics.filter(t => lower.includes(t.toLowerCase()))
    const coverage = expectedTopics.length > 0 ? hits.length / expectedTopics.length : 0

    // Also check against sample answer keywords
    const sampleWords = sampleAnswer.toLowerCase().split(/\W+/).filter(w => w.length > 4)
    const sampleHits = sampleWords.filter(w => lower.includes(w)).length
    const sampleCoverage = sampleWords.length > 0 ? Math.min(1, sampleHits / (sampleWords.length * 0.4)) : 0

    const score = Math.round(((coverage * 0.6 + sampleCoverage * 0.4)) * 100)
    const clampedScore = Math.max(0, Math.min(100, score))

    let feedback = ''
    if (clampedScore >= 80) {
      feedback = `Excellent! You covered the key concepts well.`
    } else if (clampedScore >= 50) {
      const missing = expectedTopics.filter(t => !lower.includes(t.toLowerCase()))
      feedback = `Good start! Consider also mentioning: ${missing.slice(0, 3).join(', ')}.`
    } else {
      feedback = `Try to cover: ${expectedTopics.slice(0, 4).join(', ')}. Review the sample answer for guidance.`
    }

    return { score: clampedScore, feedback }
  }

  const handleSelfEval = (key: string, q: any) => {
    const answer = qState[key]?.userAnswer?.trim()
    if (!answer || answer.length < 10) {
      toast.error('Write at least a sentence before evaluating')
      return
    }
    updateQ(key, { evalStatus: 'evaluating' })

    // Small async delay to show spinner, then deterministic eval
    setTimeout(() => {
      try {
        const { score, feedback } = evaluateAnswer(
          answer,
          q.sample_answer || '',
          q.expected_topics || [],
        )
        updateQ(key, { evalStatus: 'done', evalScore: score, evalFeedback: feedback })
      } catch {
        updateQ(key, { evalStatus: 'error', evalFeedback: 'Evaluation failed. Review the sample answer manually.' })
      }
    }, 600)
  }

  const TYPE_COLOR: Record<string, string> = {
    conceptual: 'bg-blue-500/10 text-blue-300',
    coding: 'bg-green-500/10 text-green-300',
    behavioral: 'bg-purple-500/10 text-purple-300',
    system_design: 'bg-orange-500/10 text-orange-300',
    technical: 'bg-cyan-500/10 text-cyan-300',
    scenario: 'bg-yellow-500/10 text-yellow-300',
    'problem-solving': 'bg-rose-500/10 text-rose-300',
  }

  const totalQuestions = interview?.sections?.reduce(
    (acc: number, s: any) => acc + (s.questions?.length ?? 0), 0,
  ) ?? 0
  const answeredCount = Object.values(qState).filter(s => s.evalStatus === 'done').length
  const progress = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <Mic className="w-6 h-6 text-accent-400" /> Mock Interview
      </h1>

      {/* ── Config ─────────────────────────────────────────────────────── */}
      <div className="glass-card p-6 mb-6">
        <div className="grid sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Target Role</label>
            <select
              value={ROLES.includes(role) ? role : ''}
              onChange={e => setRole(e.target.value)}
              className="input-field mb-2"
            >
              <option value="">Select a role…</option>
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <input
              value={role}
              onChange={e => setRole(e.target.value)}
              placeholder="Or type a custom role…"
              className="input-field"
              aria-label="Custom role input"
            />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Difficulty</label>
            <div className="grid grid-cols-3 gap-2 mb-3">
              {DIFFICULTIES.map(d => (
                <button
                  key={d}
                  onClick={() => setDifficulty(d)}
                  className={`py-2 rounded-xl text-sm font-medium capitalize border transition-all ${
                    difficulty === d
                      ? 'border-accent-500 bg-accent-500/20 text-accent-300'
                      : 'border-white/10 bg-white/5 text-gray-400 hover:border-accent-500/30'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1.5 block">
                Questions per section
              </label>
              <div className="grid grid-cols-4 gap-2">
                {QUESTION_COUNTS.map(n => (
                  <button
                    key={n}
                    onClick={() => setNumQuestions(n)}
                    className={`py-1.5 rounded-lg text-sm border transition-all ${
                      numQuestions === n
                        ? 'border-accent-500 bg-accent-500/20 text-accent-300'
                        : 'border-white/10 bg-white/5 text-gray-500 hover:border-accent-500/20'
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => mutation.mutate()}
            disabled={!role || mutation.isPending}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {mutation.isPending
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Brain className="w-4 h-4" />}
            Generate Interview Questions
          </button>
          {interview && (
            <button
              onClick={() => setPracticeMode(p => !p)}
              className={`btn-secondary flex items-center gap-2 ${practiceMode ? 'border-accent-500/50 text-accent-300' : ''}`}
              title="Toggle practice mode to write and self-evaluate your answers"
            >
              <BookOpen className="w-4 h-4" />
              {practiceMode ? 'Hide Practice' : 'Practice Mode'}
            </button>
          )}
        </div>

        {practiceMode && (
          <p className="text-xs text-gray-500 mt-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />
            Practice mode: type your answer to each question and get instant feedback
          </p>
        )}
      </div>

      {/* Error state */}
      {mutation.isError && (
        <div className="glass-card p-4 mb-6 border border-red-500/20 bg-red-500/5 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-red-300 font-medium">Failed to generate questions</p>
            <p className="text-xs text-gray-400 mt-1">
              Make sure a role is selected and the backend is running.
            </p>
            <button
              onClick={() => mutation.mutate()}
              className="text-xs text-primary-400 hover:text-primary-300 mt-1.5 flex items-center gap-1"
            >
              Try again <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}

      {/* Progress bar (practice mode only) */}
      {interview && practiceMode && totalQuestions > 0 && (
        <div className="glass-card p-4 mb-4">
          <div className="flex justify-between text-xs text-gray-500 mb-1.5">
            <span>{answeredCount} of {totalQuestions} answered</span>
            <span>{progress}%</span>
          </div>
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-accent-500 to-primary-500 rounded-full"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
          {progress === 100 && (
            <p className="text-xs text-green-400 mt-1.5 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              All questions attempted! Review sample answers to refine your responses.
            </p>
          )}
        </div>
      )}

      {interview && (
        <div className="space-y-5">
          {/* Tips */}
          {interview.tips?.length > 0 && (
            <div className="glass-card p-4">
              <p className="text-sm font-semibold text-primary-300 mb-2">💡 Interview Tips</p>
              <ul className="space-y-1">
                {interview.tips.map((t: string, i: number) => (
                  <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                    <span className="text-primary-400">•</span> {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sections */}
          {interview.sections?.map((section: any, si: number) => (
            <div key={si} className="glass-card p-5">
              <h2 className="font-semibold text-white mb-4">{section.category}</h2>
              <div className="space-y-3">
                {section.questions?.map((q: any, qi: number) => {
                  const key = getQKey(si, qi)
                  const qs = qState[key]
                  const isExpanded = qs?.expanded ?? false
                  const evalStatus = qs?.evalStatus ?? 'idle'
                  const score = qs?.evalScore

                  return (
                    <div key={qi} className="bg-white/5 rounded-xl overflow-hidden">
                      <button
                        onClick={() => toggleExpand(key)}
                        className="w-full text-left p-3.5 flex items-start justify-between gap-3"
                        aria-expanded={isExpanded}
                      >
                        <div className="flex items-start gap-2.5 flex-1">
                          <span className="text-primary-400 text-sm font-mono mt-0.5">{qi + 1}.</span>
                          <div className="flex-1">
                            <div className="flex flex-wrap gap-1.5 mb-1">
                              <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${TYPE_COLOR[q.type] || 'bg-gray-500/10 text-gray-400'}`}>
                                {q.type}
                              </span>
                              <span className={`text-xs px-1.5 py-0.5 rounded ${
                                q.difficulty === 'easy' ? 'bg-green-500/10 text-green-400' :
                                q.difficulty === 'hard' ? 'bg-red-500/10 text-red-400' :
                                'bg-yellow-500/10 text-yellow-400'
                              }`}>{q.difficulty}</span>
                              {/* Score badge when evaluated */}
                              {evalStatus === 'done' && score !== null && (
                                <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${
                                  score >= 70 ? 'bg-green-500/20 text-green-300' :
                                  score >= 40 ? 'bg-yellow-500/20 text-yellow-300' :
                                  'bg-red-500/20 text-red-300'
                                }`}>
                                  {score}%
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-white">{q.question}</p>
                          </div>
                        </div>
                        {isExpanded
                          ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
                      </button>

                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="px-4 pb-4 border-t border-white/10 pt-3 space-y-3">
                              {/* Practice answer textarea */}
                              {practiceMode && (
                                <div>
                                  <label className="text-xs font-semibold text-accent-300 mb-1.5 block">
                                    Your Answer
                                  </label>
                                  <textarea
                                    value={qs?.userAnswer ?? ''}
                                    onChange={e => updateQ(key, { userAnswer: e.target.value })}
                                    placeholder="Write your answer here before revealing the sample answer…"
                                    rows={4}
                                    className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-gray-300 placeholder-gray-600 focus:outline-none focus:border-accent-500/50 resize-none"
                                    disabled={evalStatus === 'done'}
                                  />
                                  <div className="flex items-center gap-2 mt-2">
                                    <button
                                      onClick={() => handleSelfEval(key, q)}
                                      disabled={evalStatus === 'evaluating' || evalStatus === 'done' || !qs?.userAnswer?.trim()}
                                      className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5"
                                    >
                                      {evalStatus === 'evaluating'
                                        ? <><Loader2 className="w-3 h-3 animate-spin" /> Evaluating…</>
                                        : evalStatus === 'done'
                                        ? <><CheckCircle2 className="w-3 h-3 text-green-300" /> Evaluated</>
                                        : 'Self-Evaluate'}
                                    </button>
                                    {evalStatus === 'done' && (
                                      <button
                                        onClick={() => updateQ(key, { userAnswer: '', evalStatus: 'idle', evalFeedback: null, evalScore: null })}
                                        className="text-xs text-gray-500 hover:text-gray-300"
                                      >
                                        Try again
                                      </button>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* Evaluation feedback */}
                              <AnimatePresence>
                                {evalStatus === 'done' && qs?.evalFeedback && (
                                  <motion.div
                                    initial={{ opacity: 0, y: -4 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`p-3 rounded-xl border text-sm ${
                                      (qs.evalScore ?? 0) >= 70
                                        ? 'bg-green-500/10 border-green-500/20 text-green-300'
                                        : (qs.evalScore ?? 0) >= 40
                                        ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-300'
                                        : 'bg-red-500/10 border-red-500/20 text-red-300'
                                    }`}
                                  >
                                    <p className="font-semibold mb-1">
                                      {(qs.evalScore ?? 0) >= 70 ? '✅' : (qs.evalScore ?? 0) >= 40 ? '🔶' : '🔴'} Score: {qs.evalScore}%
                                    </p>
                                    <p className="text-xs leading-relaxed">{qs.evalFeedback}</p>
                                  </motion.div>
                                )}
                              </AnimatePresence>

                              {/* Sample answer */}
                              {q.sample_answer && (
                                <div>
                                  <p className="text-xs font-semibold text-primary-300 mb-1.5">
                                    {practiceMode ? '📖 Sample Answer / Key Points:' : 'Key points to cover:'}
                                  </p>
                                  <p className="text-sm text-gray-300">{q.sample_answer}</p>
                                  {q.expected_topics?.length > 0 && (
                                    <div className="flex flex-wrap gap-1.5 mt-2">
                                      {q.expected_topics.map((t: string) => (
                                        <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400">
                                          {t}
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
