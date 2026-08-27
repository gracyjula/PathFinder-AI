import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Brain, Zap, Target, TrendingUp, Users, Star, ArrowRight, Sparkles, BookOpen, Award } from 'lucide-react'

const DEMO_MESSAGES = [
  { role: 'user', text: "I'm a 2nd year AIML student. I know Python and basic ML. I want to become an AI Engineer in 12 months." },
  { role: 'ai', text: "🎯 **Goal Identified: AI Engineer (12 months)**\n\nBased on your profile, here's what I found:\n\n✅ **You have:** Python, Basic ML\n❌ **You need:** Deep Learning, NLP, Transformers, LangChain, MLOps\n\n**Gap: 68%** — but completely closeable in your timeline!\n\nGenerating your personalized 12-month roadmap..." },
]

const FEATURES = [
  { icon: Brain, title: 'AI Mentor', desc: 'Personal AI mentor that guides you daily, answers questions, and keeps you on track', color: 'from-blue-500 to-cyan-500' },
  { icon: Target, title: 'Skill Gap Analysis', desc: 'Instantly identify what skills you need for your dream role with precision gap reports', color: 'from-purple-500 to-pink-500' },
  { icon: Zap, title: 'Adaptive Roadmaps', desc: 'Dynamic learning paths that evolve with your progress and adapt to your pace', color: 'from-yellow-500 to-orange-500' },
  { icon: TrendingUp, title: 'Career Readiness', desc: 'Real-time career readiness score with actionable suggestions to improve', color: 'from-green-500 to-emerald-500' },
  { icon: BookOpen, title: 'Curated Resources', desc: 'AI-picked courses, videos, papers and projects perfectly matched to your stage', color: 'from-red-500 to-rose-500' },
  { icon: Award, title: 'Mock Interviews', desc: 'AI-generated mock interviews with evaluation and feedback for your target role', color: 'from-indigo-500 to-violet-500' },
]

const GOALS = [
  'Become AI Engineer', 'Crack GATE CSE', 'Become Data Scientist',
  'Full Stack Developer', 'Learn Generative AI', 'Cloud Engineer',
  'Product-Based Companies', 'Cybersecurity Expert',
]

export default function LandingPage() {
  const [inputValue, setInputValue] = useState('')
  const [showDemo, setShowDemo] = useState(false)

  return (
    <div className="min-h-screen text-white overflow-x-hidden" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>
      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 backdrop-blur-md bg-black/20 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-xl gradient-text">NeuraLearn AI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="btn-secondary text-sm py-2">Sign In</Link>
          <Link to="/register" className="btn-primary text-sm py-2">Get Started Free</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6 text-center relative">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-1/4 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="relative max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-300 text-sm mb-6">
            <Sparkles className="w-4 h-4" />
            <span>AI-Powered Learning Operating System</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
            Your Personal{' '}
            <span className="gradient-text">AI Learning</span>
            <br />
            Mentor & Roadmap
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            Tell NeuraLearn your goal. Get a complete personalized roadmap, skill gap analysis,
            curated resources, and an AI mentor — all in one platform.
          </p>

          {/* CTA Input */}
          <div className="max-w-2xl mx-auto mb-8">
            <div className="flex flex-col sm:flex-row gap-3 glass-card p-2">
              <input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="I want to become an AI Engineer in 12 months..."
                className="flex-1 bg-transparent px-4 py-3 text-white placeholder-gray-500 outline-none text-sm"
                onFocus={() => setShowDemo(true)}
              />
              <Link
                to="/register"
                className="btn-primary flex items-center gap-2 justify-center whitespace-nowrap"
              >
                Build My Roadmap <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Goal pills */}
          <div className="flex flex-wrap gap-2 justify-center mb-4">
            {GOALS.map((goal) => (
              <button
                key={goal}
                onClick={() => setInputValue(goal)}
                className="px-3 py-1.5 text-xs rounded-full bg-white/5 border border-white/10 text-gray-300 hover:border-primary-500/40 hover:text-white transition-all"
              >
                {goal}
              </button>
            ))}
          </div>
        </motion.div>

        {/* Demo Chat Preview */}
        {showDemo && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-2xl mx-auto mt-8 glass-card p-4 text-left"
          >
            <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
              <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-xs text-gray-400">NeuraLearn AI • Demo</span>
            </div>
            {DEMO_MESSAGES.map((msg, i) => (
              <div key={i} className={`mb-3 ${msg.role === 'user' ? 'flex justify-end' : ''}`}>
                {msg.role === 'ai' && (
                  <div className="flex items-start gap-2 mb-1">
                    <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex-shrink-0 flex items-center justify-center mt-0.5">
                      <Brain className="w-3 h-3 text-white" />
                    </div>
                    <div className="glass-card px-3 py-2 text-sm text-gray-200 whitespace-pre-line max-w-md">
                      {msg.text}
                    </div>
                  </div>
                )}
                {msg.role === 'user' && (
                  <div className="bg-primary-600/30 border border-primary-500/30 rounded-2xl rounded-tr-sm px-3 py-2 text-sm text-gray-100 max-w-sm">
                    {msg.text}
                  </div>
                )}
              </div>
            ))}
          </motion.div>
        )}
      </section>

      {/* Stats */}
      <section className="py-10 px-6">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { value: '10+', label: 'Career Paths' },
            { value: '50+', label: 'Skills Tracked' },
            { value: '100+', label: 'Curated Resources' },
            { value: 'AI', label: 'Powered by Gemini' },
          ].map((stat) => (
            <div key={stat.label} className="glass-card p-5 text-center">
              <div className="text-3xl font-bold gradient-text mb-1">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="text-4xl font-bold mb-4">Everything you need to level up</h2>
            <p className="text-gray-400 text-lg">Netflix + Duolingo + Coursera + ChatGPT + Career Coach — in one platform</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass-card-hover p-6"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4`}>
                  <f.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto text-center glass-card p-10">
          <Brain className="w-12 h-12 text-primary-400 mx-auto mb-4" />
          <h2 className="text-3xl font-bold mb-4">Start your learning journey today</h2>
          <p className="text-gray-400 mb-8">Join learners who are using AI to accelerate their careers</p>
          <Link to="/register" className="btn-primary inline-flex items-center gap-2">
            Get Started Free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6 text-center text-gray-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Brain className="w-4 h-4 text-primary-400" />
          <span className="gradient-text font-semibold">NeuraLearn AI</span>
        </div>
        <p>Built for HCL Hackathon 2026 • Powered by Gemini AI</p>
      </footer>
    </div>
  )
}
