import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, ArrowRight, ArrowLeft, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const SKILLS_POOL = [
  'Python', 'JavaScript', 'Java', 'C++', 'SQL', 'Machine Learning', 'Deep Learning',
  'NLP', 'React', 'Node.js', 'Docker', 'AWS', 'Data Structures', 'System Design',
  'MongoDB', 'TensorFlow', 'PyTorch', 'Git', 'Linux', 'TypeScript',
  'Statistics', 'Mathematics', 'Generative AI', 'MLOps', 'Data Analysis',
]

const INTERESTS = ['AI/ML', 'Web Development', 'Data Science', 'Cloud', 'Cybersecurity', 'Mobile Dev', 'DevOps', 'Blockchain']
const GOALS = ['AI Engineer', 'ML Engineer', 'Data Scientist', 'Full Stack Developer', 'Cloud Engineer', 'Software Engineer', 'Crack GATE CSE', 'Data Analyst', 'Generative AI Engineer', 'Backend Developer', 'DevOps Engineer']
const LEARNING_STYLES = [
  { value: 'visual', label: 'Visual', desc: 'Videos, diagrams, charts' },
  { value: 'reading', label: 'Reading', desc: 'Articles, books, docs' },
  { value: 'hands_on', label: 'Hands-on', desc: 'Projects, coding, building' },
  { value: 'mixed', label: 'Mixed', desc: 'Combination of all' },
]

const STEPS = ['Personal Info', 'Your Goal', 'Current Skills', 'Learning Style', 'Done']

export default function OnboardingPage() {
  const navigate = useNavigate()
  const { fetchProfile } = useAuthStore()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [customSkill, setCustomSkill] = useState('')
  const [data, setData] = useState({
    education: '', degree: '', year_of_study: 2, institution: '',
    career_goal: '', target_timeline_months: 12, learning_goal: '',
    current_skills: [] as string[], interests: [] as string[],
    learning_style: 'mixed', weekly_hours: 10, preferred_difficulty: 'beginner',
    experience_level: 'beginner',
  })

  const toggle = (field: 'current_skills' | 'interests', val: string) => {
    setData(d => ({
      ...d,
      [field]: d[field].includes(val)
        ? d[field].filter(v => v !== val)
        : [...d[field], val],
    }))
  }

  const addCustomSkill = () => {
    const s = customSkill.trim()
    if (s && !data.current_skills.includes(s)) {
      setData(d => ({ ...d, current_skills: [...d.current_skills, s] }))
      setCustomSkill('')
    }
  }

  const handleNext = () => {
    if (step === 1 && !data.career_goal.trim()) {
      toast.error('Please select or type a career goal before continuing')
      return
    }
    setStep(s => s + 1)
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      await api.post('/profile', data)
      await fetchProfile()
      toast.success('Profile created! Generating your roadmap...')
      navigate('/dashboard/chat')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Failed to save profile')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-10" style={{ background: 'var(--bg-base)' }}>
      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Brain className="w-8 h-8 text-primary-400" />
            <span className="font-bold text-xl gradient-text">NeuraLearn AI</span>
          </div>
          <h1 className="text-2xl font-bold mb-2">Let's personalize your experience</h1>
          <p className="text-gray-400 text-sm">Tell us about yourself so we can build your perfect roadmap</p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {STEPS.map((s, i) => (
            <div key={s} className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                i < step ? 'bg-primary-500 text-white' :
                i === step ? 'bg-primary-500/20 border-2 border-primary-500 text-primary-400' :
                'bg-white/5 border border-white/20 text-gray-500'
              }`}>
                {i < step ? <Check className="w-3 h-3" /> : i + 1}
              </div>
              {i < STEPS.length - 1 && (
                <div className={`w-8 h-0.5 ${i < step ? 'bg-primary-500' : 'bg-white/10'}`} />
              )}
            </div>
          ))}
        </div>

        <div className="glass-card p-7">
          <AnimatePresence mode="wait">
            {/* Step 0: Personal Info */}
            {step === 0 && (
              <motion.div key="step0" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-lg font-semibold mb-5">Tell us about yourself</h2>
                <div className="space-y-4">
                  <input value={data.education} onChange={e => setData(d => ({ ...d, education: e.target.value }))}
                    placeholder="e.g. B.Tech AI & ML" className="input-field" />
                  <input value={data.institution} onChange={e => setData(d => ({ ...d, institution: e.target.value }))}
                    placeholder="Institution / College name" className="input-field" />
                  <div className="grid grid-cols-2 gap-3">
                    <select value={data.year_of_study} onChange={e => setData(d => ({ ...d, year_of_study: +e.target.value }))}
                      className="input-field">
                      {[1, 2, 3, 4, 5].map(y => <option key={y} value={y}>Year {y}</option>)}
                    </select>
                    <select value={data.experience_level} onChange={e => setData(d => ({ ...d, experience_level: e.target.value }))}
                      className="input-field">
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Step 1: Goal */}
            {step === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-lg font-semibold mb-5">What's your goal?</h2>
                <div className="grid grid-cols-2 gap-2 mb-4">
                  {GOALS.map(g => (
                    <button key={g} onClick={() => setData(d => ({ ...d, career_goal: g }))}
                      className={`p-3 rounded-xl text-sm text-left transition-all border ${
                        data.career_goal === g
                          ? 'border-primary-500 bg-primary-500/20 text-white'
                          : 'border-white/10 bg-white/5 text-gray-300 hover:border-primary-500/30'
                      }`}>
                      {g}
                    </button>
                  ))}
                </div>
                <input value={data.career_goal} onChange={e => setData(d => ({ ...d, career_goal: e.target.value }))}
                  placeholder="Or type your own goal..." className="input-field mb-3" />
                <div className="flex items-center gap-3">
                  <label className="text-sm text-gray-400 whitespace-nowrap">Timeline:</label>
                  <select value={data.target_timeline_months} onChange={e => setData(d => ({ ...d, target_timeline_months: +e.target.value }))}
                    className="input-field">
                    {[3, 6, 9, 12, 18, 24].map(m => <option key={m} value={m}>{m} months</option>)}
                  </select>
                </div>
              </motion.div>
            )}

            {/* Step 2: Skills & Interests */}
            {step === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-lg font-semibold mb-2">Current Skills</h2>
                <p className="text-gray-400 text-sm mb-4">Select all that apply</p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {SKILLS_POOL.map(skill => (
                    <button key={skill} onClick={() => toggle('current_skills', skill)}
                      className={`px-3 py-1.5 rounded-full text-sm transition-all border ${
                        data.current_skills.includes(skill)
                          ? 'bg-primary-500/20 border-primary-500 text-primary-300'
                          : 'bg-white/5 border-white/10 text-gray-400 hover:border-primary-500/30'
                      }`}>
                      {skill}
                    </button>
                  ))}
                </div>
                {/* Custom skill input */}
                <div className="flex gap-2 mb-6">
                  <input
                    value={customSkill}
                    onChange={e => setCustomSkill(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && addCustomSkill()}
                    placeholder="Add a custom skill…"
                    className="input-field py-2 text-sm flex-1"
                  />
                  <button onClick={addCustomSkill} disabled={!customSkill.trim()} className="btn-secondary py-2 px-3 text-sm">Add</button>
                </div>
                {/* Show any custom skills added */}
                {data.current_skills.filter(s => !SKILLS_POOL.includes(s)).length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {data.current_skills.filter(s => !SKILLS_POOL.includes(s)).map(skill => (
                      <button key={skill} onClick={() => toggle('current_skills', skill)}
                        className="px-3 py-1.5 rounded-full text-sm bg-accent-500/20 border border-accent-500 text-accent-300">
                        {skill} ✕
                      </button>
                    ))}
                  </div>
                )}
                <h2 className="text-lg font-semibold mb-2">Interests</h2>
                <div className="flex flex-wrap gap-2">
                  {INTERESTS.map(i => (
                    <button key={i} onClick={() => toggle('interests', i)}
                      className={`px-3 py-1.5 rounded-full text-sm transition-all border ${
                        data.interests.includes(i)
                          ? 'bg-accent-500/20 border-accent-500 text-accent-300'
                          : 'bg-white/5 border-white/10 text-gray-400 hover:border-accent-500/30'
                      }`}>
                      {i}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {/* Step 3: Learning Style */}
            {step === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                <h2 className="text-lg font-semibold mb-5">How do you learn best?</h2>
                <div className="grid grid-cols-2 gap-3 mb-5">
                  {LEARNING_STYLES.map(s => (
                    <button key={s.value} onClick={() => setData(d => ({ ...d, learning_style: s.value }))}
                      className={`p-4 rounded-xl text-left transition-all border ${
                        data.learning_style === s.value
                          ? 'border-primary-500 bg-primary-500/20'
                          : 'border-white/10 bg-white/5 hover:border-primary-500/30'
                      }`}>
                      <div className="font-medium text-white mb-0.5">{s.label}</div>
                      <div className="text-xs text-gray-400">{s.desc}</div>
                    </button>
                  ))}
                </div>
                <div className="flex items-center gap-3">
                  <label className="text-sm text-gray-400 whitespace-nowrap">Weekly hours:</label>
                  <input type="number" min={1} max={40} value={data.weekly_hours}
                    onChange={e => setData(d => ({ ...d, weekly_hours: +e.target.value }))}
                    className="input-field w-24" />
                  <span className="text-gray-400 text-sm">hrs/week</span>
                </div>
              </motion.div>
            )}

            {/* Step 4: Done */}
            {step === 4 && (
              <motion.div key="step4" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }}
                className="text-center py-6">
                <div className="w-16 h-16 rounded-full bg-primary-500/20 border-2 border-primary-500 flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-primary-400" />
                </div>
                <h2 className="text-xl font-bold mb-2">All set, {data.career_goal ? `future ${data.career_goal}` : 'learner'}! 🎉</h2>
                <p className="text-gray-400 text-sm mb-6">We're ready to build your personalized AI roadmap</p>
                <div className="glass-card p-4 text-left text-sm space-y-2 mb-6">
                  <div className="flex justify-between"><span className="text-gray-400">Goal</span><span className="text-white font-medium">{data.career_goal || '—'}</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Timeline</span><span className="text-white font-medium">{data.target_timeline_months} months</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Skills</span><span className="text-white font-medium">{data.current_skills.length} selected</span></div>
                  <div className="flex justify-between"><span className="text-gray-400">Style</span><span className="text-white font-medium capitalize">{data.learning_style}</span></div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between mt-6">
            <button onClick={() => setStep(s => Math.max(0, s - 1))} disabled={step === 0}
              className="btn-secondary flex items-center gap-2 disabled:opacity-30">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>
            {step < 4 ? (
              <button onClick={handleNext} className="btn-primary flex items-center gap-2">
                Next <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button onClick={handleSubmit} disabled={loading} className="btn-primary flex items-center gap-2">
                {loading ? 'Saving...' : 'Build My Roadmap'} <ArrowRight className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
