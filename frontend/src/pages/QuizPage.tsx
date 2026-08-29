import { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Brain, CheckCircle2, XCircle, Loader2, RotateCcw, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import type { QuizResult } from '@/types'

const TOPICS = [
  'Python', 'Machine Learning', 'Deep Learning', 'NLP', 'Transformers',
  'Generative AI', 'MLOps', 'Docker', 'Statistics', 'Data Structures',
  'System Design', 'LangChain', 'SQL', 'Cloud',
]

export default function QuizPage() {
  const location = useLocation()
  const qc = useQueryClient()
  const prefill = (location.state as any)?.prefillTopic ?? ''

  const [topic, setTopic] = useState(prefill)
  const [difficulty, setDifficulty] = useState('intermediate')
  const [quiz, setQuiz] = useState<any>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<QuizResult | null>(null)

  const generateMutation = useMutation({
    mutationFn: () => api.post('/analytics/quiz/generate', { topic, difficulty, num_questions: 5 }),
    onSuccess: (res) => {
      setQuiz(res.data)
      setAnswers({})
      setSubmitted(false)
      setResult(null)
    },
    onError: () => toast.error('Failed to generate quiz'),
  })

  const submitMutation = useMutation({
    mutationFn: () => api.post('/analytics/quiz/submit', { topic, answers, questions: quiz }),
    onSuccess: (res) => {
      setResult(res.data)
      setSubmitted(true)
      // Invalidate mastery-dependent queries so dashboard updates
      qc.invalidateQueries({ queryKey: ['mastery'] })
      qc.invalidateQueries({ queryKey: ['skill-gap-current'] })
      qc.invalidateQueries({ queryKey: ['next-best-action'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: () => toast.error('Failed to submit quiz'),
  })

  const allAnswered = quiz?.questions?.length > 0 && Object.keys(answers).length === quiz.questions.length

  const masteryDelta = result?.mastery_update?.delta ?? 0
  const MasteryIcon = masteryDelta > 0 ? TrendingUp : masteryDelta < 0 ? TrendingDown : Minus
  const masteryColor = masteryDelta > 0 ? 'text-green-400' : masteryDelta < 0 ? 'text-red-400' : 'text-gray-400'

  // Auto-generate quiz when navigated from Next Best Action with a prefilled topic
  useEffect(() => {
    if (prefill && topic === prefill && !quiz && !generateMutation.isPending) {
      generateMutation.mutate()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <Brain className="w-6 h-6 text-primary-400" /> Knowledge Quiz
      </h1>

      {!quiz ? (
        <div className="glass-card p-6">
          <h2 className="font-semibold mb-4 text-white">Select a topic</h2>
          <div className="flex flex-wrap gap-2 mb-5">
            {TOPICS.map(t => (
              <button key={t} onClick={() => setTopic(t)}
                className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                  topic === t
                    ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                    : 'border-white/10 bg-white/5 text-gray-400 hover:border-primary-500/30'
                }`}>
                {t}
              </button>
            ))}
          </div>
          <input
            value={topic}
            onChange={e => setTopic(e.target.value)}
            placeholder="Or type a custom topic…"
            className="input-field mb-4"
          />
          <div className="flex gap-3 mb-5">
            {['beginner', 'intermediate', 'advanced'].map(d => (
              <button key={d} onClick={() => setDifficulty(d)}
                className={`flex-1 py-2 rounded-xl text-sm font-medium capitalize border transition-all ${
                  difficulty === d
                    ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                    : 'border-white/10 bg-white/5 text-gray-400'
                }`}>
                {d}
              </button>
            ))}
          </div>
          <button
            onClick={() => generateMutation.mutate()}
            disabled={!topic || generateMutation.isPending}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
            Generate Quiz
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Quiz header */}
          <div className="glass-card p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <p className="font-semibold text-white">{quiz.topic} Quiz</p>
                <p className="text-sm text-gray-400 capitalize">{quiz.difficulty} • {quiz.questions?.length} questions</p>
              </div>
              <button onClick={() => setQuiz(null)} className="btn-secondary flex items-center gap-1.5 text-sm py-2" aria-label="Start a new quiz">
                <RotateCcw className="w-3.5 h-3.5" /> New Quiz
              </button>
            </div>
            {/* Progress bar showing answered count */}
            {!submitted && (
              <div>
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>{Object.keys(answers).length} of {quiz.questions?.length} answered</span>
                  <span>{Math.round((Object.keys(answers).length / (quiz.questions?.length || 1)) * 100)}%</span>
                </div>
                <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-300"
                    style={{ width: `${(Object.keys(answers).length / (quiz.questions?.length || 1)) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Result + mastery update banner */}
          <AnimatePresence>
            {submitted && result && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className={`glass-card p-4 border ${result.passed ? 'border-green-500/40' : 'border-red-500/40'}`}
              >
                {/* Score row */}
                <div className="flex items-center gap-3 mb-3">
                  {result.passed
                    ? <CheckCircle2 className="w-6 h-6 text-green-400 flex-shrink-0" />
                    : <XCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
                  }
                  <div>
                    <p className="font-semibold text-white">{result.passed ? '🎉 Passed!' : '📚 Keep practicing'}</p>
                    <p className="text-sm text-gray-400">Score: {result.score}% ({result.correct}/{result.total} correct)</p>
                  </div>
                </div>

                {/* Mastery update — the adaptive loop made visible */}
                {result.mastery_update && (
                  <div className="rounded-xl bg-white/5 p-3 border border-white/10">
                    <p className="text-xs font-semibold text-gray-300 mb-2 flex items-center gap-1.5">
                      <MasteryIcon className={`w-3.5 h-3.5 ${masteryColor}`} />
                      Skill Mastery Updated
                    </p>
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-400">{result.mastery_update.skill}</span>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-500">{result.mastery_update.old_mastery}%</span>
                        <span className="text-gray-600">→</span>
                        <span className={`font-semibold ${masteryColor}`}>{result.mastery_update.new_mastery}%</span>
                        <span className={`text-xs ${masteryColor}`}>
                          ({masteryDelta > 0 ? '+' : ''}{masteryDelta.toFixed(1)})
                        </span>
                      </div>
                    </div>
                    {/* Visual progress bar change */}
                    <div className="mt-2 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${result.passed ? 'bg-green-500' : 'bg-red-500'}`}
                        initial={{ width: `${result.mastery_update.old_mastery}%` }}
                        animate={{ width: `${result.mastery_update.new_mastery}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1.5">
                      Your roadmap and next best actions have been updated based on this result.
                    </p>
                  </div>
                )}

                {/* Path Updated banner — shown when adaptation triggered */}
                {result.adaptation?.triggered && result.adaptation.explanation && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl p-3 border"
                    style={{ background: 'rgba(99,102,241,0.12)', borderColor: 'rgba(99,102,241,0.3)' }}
                  >
                    <p className="text-xs font-semibold text-indigo-300 mb-1.5 flex items-center gap-1.5">
                      🔄 Your Learning Path Has Adapted
                    </p>
                    <p className="text-xs text-gray-300 leading-relaxed">{result.adaptation.explanation}</p>
                  </motion.div>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Questions */}
          {quiz.questions?.map((q: any, qi: number) => (
            <div
              key={q.id}
              className={`glass-card p-5 ${
                submitted && answers[q.id] === q.correct_answer ? 'border-green-500/20' :
                submitted ? 'border-red-500/20' : ''
              }`}
            >
              <p className="font-medium text-white mb-3">
                <span className="text-primary-400 mr-2">{qi + 1}.</span>{q.question}
              </p>
              <div className="space-y-2">
                {q.options?.map((opt: string) => {
                  const isSelected = answers[q.id] === opt
                  const isCorrect = submitted && opt === q.correct_answer
                  const isWrong = submitted && isSelected && opt !== q.correct_answer
                  return (
                    <button
                      key={opt}
                      onClick={() => !submitted && setAnswers(a => ({ ...a, [q.id]: opt }))}
                      disabled={submitted}
                      className={`w-full text-left px-4 py-2.5 rounded-xl text-sm border transition-all ${
                        isCorrect ? 'border-green-500 bg-green-500/20 text-green-300' :
                        isWrong ? 'border-red-500 bg-red-500/20 text-red-300' :
                        isSelected ? 'border-primary-500 bg-primary-500/20 text-primary-300' :
                        'border-white/10 bg-white/5 text-gray-300 hover:border-primary-500/30'
                      }`}
                    >
                      {opt}
                    </button>
                  )
                })}
              </div>
              {submitted && q.explanation && (
                <p className="mt-3 text-xs text-gray-400 bg-white/5 rounded-lg p-2.5">
                  💡 {q.explanation}
                </p>
              )}
            </div>
          ))}

          {!submitted && (
            <button
              onClick={() => submitMutation.mutate()}
              disabled={!allAnswered || submitMutation.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {submitMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Submit Answers'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
