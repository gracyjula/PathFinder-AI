import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Mic, ChevronDown, ChevronUp, Loader2, Brain } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const ROLES = ['AI Engineer', 'Data Scientist', 'Full Stack Developer', 'Backend Developer', 'ML Engineer', 'Cloud Engineer', 'DevOps Engineer']
const DIFFICULTIES = ['easy', 'intermediate', 'hard']

export default function InterviewPage() {
  const { profile } = useAuthStore()
  const [role, setRole] = useState(profile?.career_goal || '')
  const [difficulty, setDifficulty] = useState('intermediate')
  const [interview, setInterview] = useState<any>(null)
  const [expanded, setExpanded] = useState<number | null>(null)

  const mutation = useMutation({
    mutationFn: () => api.post(`/analytics/mock-interview?role=${encodeURIComponent(role)}&difficulty=${difficulty}`),
    onSuccess: (res) => setInterview(res.data),
    onError: () => toast.error('Failed to generate interview questions'),
  })

  const TYPE_COLOR: Record<string, string> = {
    conceptual: 'bg-blue-500/10 text-blue-300',
    coding: 'bg-green-500/10 text-green-300',
    behavioral: 'bg-purple-500/10 text-purple-300',
    system_design: 'bg-orange-500/10 text-orange-300',
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
        <Mic className="w-6 h-6 text-accent-400" /> Mock Interview
      </h1>

      <div className="glass-card p-6 mb-6">
        <div className="grid sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Target Role</label>
            <select value={role} onChange={e => setRole(e.target.value)} className="input-field">
              <option value="">Select a role...</option>
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <input value={role} onChange={e => setRole(e.target.value)}
              placeholder="Or type a custom role..." className="input-field mt-2" />
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Difficulty</label>
            <div className="grid grid-cols-3 gap-2">
              {DIFFICULTIES.map(d => (
                <button key={d} onClick={() => setDifficulty(d)}
                  className={`py-2 rounded-xl text-sm font-medium capitalize border transition-all ${
                    difficulty === d ? 'border-accent-500 bg-accent-500/20 text-accent-300' : 'border-white/10 bg-white/5 text-gray-400'
                  }`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
        </div>
        <button onClick={() => mutation.mutate()} disabled={!role || mutation.isPending}
          className="btn-primary w-full flex items-center justify-center gap-2">
          {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
          Generate Interview Questions
        </button>
      </div>

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
                {section.questions?.map((q: any, qi: number) => (
                  <div key={qi} className="bg-white/5 rounded-xl overflow-hidden">
                    <button
                      onClick={() => setExpanded(expanded === si * 100 + qi ? null : si * 100 + qi)}
                      className="w-full text-left p-3.5 flex items-start justify-between gap-3"
                    >
                      <div className="flex items-start gap-2.5 flex-1">
                        <span className="text-primary-400 text-sm font-mono mt-0.5">{qi + 1}.</span>
                        <div className="flex-1">
                          <div className="flex flex-wrap gap-1.5 mb-1">
                            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${TYPE_COLOR[q.type] || 'bg-gray-500/10 text-gray-400'}`}>{q.type}</span>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${
                              q.difficulty === 'easy' ? 'bg-green-500/10 text-green-400' :
                              q.difficulty === 'hard' ? 'bg-red-500/10 text-red-400' : 'bg-yellow-500/10 text-yellow-400'
                            }`}>{q.difficulty}</span>
                          </div>
                          <p className="text-sm text-white">{q.question}</p>
                        </div>
                      </div>
                      {expanded === si * 100 + qi ? <ChevronUp className="w-4 h-4 text-gray-400 flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />}
                    </button>

                    {expanded === si * 100 + qi && q.sample_answer && (
                      <div className="px-4 pb-4 border-t border-white/10 pt-3">
                        <p className="text-xs font-semibold text-primary-300 mb-2">Key points to cover:</p>
                        <p className="text-sm text-gray-300">{q.sample_answer}</p>
                        {q.expected_topics?.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            {q.expected_topics.map((t: string) => (
                              <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-400">{t}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
