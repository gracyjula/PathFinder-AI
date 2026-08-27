import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Brain, CheckCircle2, XCircle, Loader2, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const TOPICS = ['Python', 'Machine Learning', 'Deep Learning', 'NLP', 'SQL', 'Data Structures', 'System Design', 'LangChain', 'React', 'Docker']

export default function QuizPage() {
  const { profile } = useAuthStore()
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [quiz, setQuiz] = useState<any>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [submitted, setSubmitted] = useState(false)
  const [result, setResult] = useState<any>(null)

  const generateMutation = useMutation({
    mutationFn: () => api.post('/analytics/quiz/generate', { topic, difficulty, num_questions: 5 }),
    onSuccess: (res) => { setQuiz(res.data); setAnswers({}); setSubmitted(false); setResult(null) },
    onError: () => toast.error('Failed to generate quiz'),
  })

  const submitMutation = useMutation({
    mutationFn: () => api.post('/analytics/quiz/submit', { topic, answers, questions: quiz }),
    onSuccess: (res) => { setResult(res.data); setSubmitted(true) },
    onError: () => toast.error('Failed to submit quiz'),
  })

  const allAnswered = quiz?.questions?.length > 0 && Object.keys(answers).length === quiz.questions.length

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <Brain className="w-6 h-6 text-primary-400" /> Knowledge Quiz
      </h1>

      {!quiz ? (
        <div className="glass-card p-6">
          <h2 className="font-semibold mb-4">Select a topic</h2>
          <div className="flex flex-wrap gap-2 mb-5">
            {TOPICS.map(t => (
              <button key={t} onClick={() => setTopic(t)}
                className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                  topic === t ? 'border-primary-500 bg-primary-500/20 text-primary-300' : 'border-white/10 bg-white/5 text-gray-400 hover:border-primary-500/30'
                }`}>
                {t}
              </button>
            ))}
          </div>
          <input value={topic} onChange={e => setTopic(e.target.value)}
            placeholder="Or type a custom topic..." className="input-field mb-4" />
          <div className="flex gap-3 mb-5">
            {['beginner', 'intermediate', 'advanced'].map(d => (
              <button key={d} onClick={() => setDifficulty(d)}
                className={`flex-1 py-2 rounded-xl text-sm font-medium capitalize border transition-all ${
                  difficulty === d ? 'border-primary-500 bg-primary-500/20 text-primary-300' : 'border-white/10 bg-white/5 text-gray-400'
                }`}>
                {d}
              </button>
            ))}
          </div>
          <button onClick={() => generateMutation.mutate()} disabled={!topic || generateMutation.isPending}
            className="btn-primary w-full flex items-center justify-center gap-2">
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
            Generate Quiz
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Quiz header */}
          <div className="glass-card p-4 flex items-center justify-between">
            <div>
              <p className="font-semibold text-white">{quiz.topic} Quiz</p>
              <p className="text-sm text-gray-400 capitalize">{quiz.difficulty} • {quiz.questions?.length} questions</p>
            </div>
            <button onClick={() => setQuiz(null)} className="btn-secondary flex items-center gap-1.5 text-sm py-2">
              <RotateCcw className="w-3.5 h-3.5" /> New Quiz
            </button>
          </div>

          {/* Result banner */}
          {submitted && result && (
            <div className={`glass-card p-4 border ${result.passed ? 'border-green-500/40' : 'border-red-500/40'}`}>
              <div className="flex items-center gap-3">
                {result.passed ? <CheckCircle2 className="w-6 h-6 text-green-400" /> : <XCircle className="w-6 h-6 text-red-400" />}
                <div>
                  <p className="font-semibold text-white">{result.passed ? '🎉 Passed!' : '📚 Keep practicing'}</p>
                  <p className="text-sm text-gray-400">Score: {result.score}% ({result.correct}/{result.total} correct)</p>
                </div>
              </div>
            </div>
          )}

          {/* Questions */}
          {quiz.questions?.map((q: any, qi: number) => (
            <div key={q.id} className={`glass-card p-5 ${submitted && answers[q.id] === q.correct_answer ? 'border-green-500/20' : submitted ? 'border-red-500/20' : ''}`}>
              <p className="font-medium text-white mb-3">
                <span className="text-primary-400 mr-2">{qi + 1}.</span>{q.question}
              </p>
              <div className="space-y-2">
                {q.options?.map((opt: string) => {
                  const isSelected = answers[q.id] === opt
                  const isCorrect = submitted && opt === q.correct_answer
                  const isWrong = submitted && isSelected && opt !== q.correct_answer
                  return (
                    <button key={opt} onClick={() => !submitted && setAnswers(a => ({ ...a, [q.id]: opt }))}
                      disabled={submitted}
                      className={`w-full text-left px-4 py-2.5 rounded-xl text-sm border transition-all ${
                        isCorrect ? 'border-green-500 bg-green-500/20 text-green-300' :
                        isWrong ? 'border-red-500 bg-red-500/20 text-red-300' :
                        isSelected ? 'border-primary-500 bg-primary-500/20 text-primary-300' :
                        'border-white/10 bg-white/5 text-gray-300 hover:border-primary-500/30'
                      }`}>
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
            <button onClick={() => submitMutation.mutate()} disabled={!allAnswered || submitMutation.isPending}
              className="btn-primary w-full flex items-center justify-center gap-2">
              {submitMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Submit Answers'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
