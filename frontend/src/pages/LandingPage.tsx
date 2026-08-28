import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Brain, ArrowRight, Target, TrendingUp, Zap, RefreshCw,
  AlertTriangle, CheckCircle2, Lightbulb, GitBranch, BarChart2, Sparkles,
} from 'lucide-react'

const CORE_LOOP = [
  { icon: '🎯', label: 'Goal' },
  { icon: '👤', label: 'Profile' },
  { icon: '🧠', label: 'Skill Analysis' },
  { icon: '🔴', label: 'Skill Gaps' },
  { icon: '🗺️', label: 'Personalized Path' },
  { icon: '💡', label: 'Why This?' },
  { icon: '📝', label: 'Assessment' },
  { icon: '📈', label: 'Mastery Update' },
  { icon: '🔄', label: 'Path Adapts' },
  { icon: '⭐', label: 'Next Best Action' },
]

const DIFFERENTIATORS = [
  {
    icon: Target,
    title: 'Skill-Gap First',
    subtitle: 'Not course-first.',
    desc: 'We analyze the gap between where you are and where you need to be before recommending anything.',
    color: 'from-rose-500 to-pink-500',
    bg: 'bg-rose-500/10',
  },
  {
    icon: GitBranch,
    title: 'Prerequisite-Aware',
    subtitle: 'Not random recommendations.',
    desc: 'A structured skill graph ensures you never attempt advanced topics before their foundations are solid.',
    color: 'from-violet-500 to-purple-500',
    bg: 'bg-violet-500/10',
  },
  {
    icon: Lightbulb,
    title: 'Explainable',
    subtitle: 'Every recommendation has a reason.',
    desc: '"Your MLOps mastery is 10% and Docker is its prerequisite — that\'s why Docker is next."',
    color: 'from-amber-500 to-orange-500',
    bg: 'bg-amber-500/10',
  },
  {
    icon: RefreshCw,
    title: 'Adaptive',
    subtitle: 'The roadmap changes as you learn.',
    desc: 'Take a quiz, get a high score, and watch your path accelerate. Score low and the system inserts reinforcement.',
    color: 'from-emerald-500 to-teal-500',
    bg: 'bg-emerald-500/10',
  },
  {
    icon: BarChart2,
    title: 'Evidence-Based Mastery',
    subtitle: 'Assessment results drive the numbers.',
    desc: 'Mastery scores come from real quiz evidence using Bayesian blending — not self-reports or AI guesses.',
    color: 'from-cyan-500 to-blue-500',
    bg: 'bg-cyan-500/10',
  },
  {
    icon: Zap,
    title: 'What-If Simulator',
    subtitle: 'Plan before you commit.',
    desc: '"What if I only have 5h/week? What if I already know Python?" Simulate changes before applying them.',
    color: 'from-indigo-500 to-primary-500',
    bg: 'bg-indigo-500/10',
  },
]

const DEMO_FLOW = [
  { before: 'Deep Learning: 40%', after: 'Deep Learning: 85%', label: 'After assessment' },
  { before: 'Next: NLP (Month 4)', after: 'Next: Transformers (Month 3)', label: 'Path accelerated' },
  { before: 'MLOps: 10%', after: 'MLOps: 10% — Added prerequisite', label: 'Reinforcement inserted' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen overflow-x-hidden" style={{ background: 'var(--bg-base)', color: 'var(--text-primary)' }}>

      {/* Nav */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 backdrop-blur-md"
        style={{ background: 'rgba(5,5,15,0.85)', borderBottom: '1px solid rgba(99,102,241,0.15)' }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-glow">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg gradient-text">NeuraLearn AI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="btn-secondary text-sm py-2 px-4">Sign In</Link>
          <Link to="/register" className="btn-primary text-sm py-2 px-4">Get Started Free</Link>
        </div>
      </nav>

      {/* ── HERO ────────────────────────────────────────────────────────────── */}
      <section className="pt-28 pb-16 px-6 text-center relative">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-1/4 w-[500px] h-[500px] rounded-full blur-3xl opacity-20"
            style={{ background: 'radial-gradient(circle, #6366f1, transparent)' }} />
          <div className="absolute top-40 right-1/4 w-[400px] h-[400px] rounded-full blur-3xl opacity-15"
            style={{ background: 'radial-gradient(circle, #a855f7, transparent)' }} />
        </div>

        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
          className="relative max-w-4xl mx-auto">

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-6 text-sm font-medium"
            style={{ background: 'rgba(99,102,241,0.12)', border: '1px solid rgba(99,102,241,0.3)', color: '#a5b4fc' }}>
            <Sparkles className="w-4 h-4" />
            PathFinder Round 2 — Adaptive AI Learning Engine
          </div>

          <h1 className="text-5xl md:text-6xl font-bold leading-tight mb-4">
            <span className="gradient-text">NeuraLearn</span> doesn't recommend courses.
          </h1>
          <h2 className="text-2xl md:text-3xl font-semibold mb-6" style={{ color: 'var(--text-secondary)' }}>
            It understands where you are, where you want to go,<br className="hidden md:block" /> and adapts your path as you improve.
          </h2>

          <p className="text-lg max-w-2xl mx-auto mb-10" style={{ color: 'var(--text-muted)' }}>
            Skill-gap analysis → prerequisite-aware roadmap → explainable recommendations → real adaptive learning.
            The path changes when <em>you</em> change.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register" className="btn-primary inline-flex items-center gap-2 py-3 px-8 text-base">
              Start Your Learning Path <ArrowRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="btn-secondary inline-flex items-center gap-2 py-3 px-8 text-base">
              Sign In
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ── THE PROBLEM ─────────────────────────────────────────────────────── */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="glass-card p-8 md:p-12"
            style={{ borderColor: 'rgba(244,63,94,0.2)', background: 'rgba(244,63,94,0.04)' }}>
            <div className="flex items-start gap-4 mb-6">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 bg-rose-500/15">
                <AlertTriangle className="w-5 h-5 text-rose-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white mb-2">The Problem</h2>
                <p className="text-gray-400 text-lg">Course recommenders tell you <em>what</em> to study. They don't know <em>why</em> you need it,
                  <em> whether you're ready for it</em>, or <em>how your plan should change</em> after you actually learn something.</p>
              </div>
            </div>
            <div className="grid md:grid-cols-3 gap-4">
              {[
                { label: 'Generic recommendations', detail: 'Same course list for everyone with the same "goal"' },
                { label: 'No prerequisite reasoning', detail: 'Recommends Deep Learning before Machine Learning basics' },
                { label: 'Static plans', detail: 'Your plan never changes, even after you demonstrate mastery' },
              ].map(p => (
                <div key={p.label} className="p-4 rounded-xl" style={{ background: 'rgba(244,63,94,0.08)', border: '1px solid rgba(244,63,94,0.15)' }}>
                  <p className="text-rose-300 font-medium text-sm mb-1">✗ {p.label}</p>
                  <p className="text-gray-500 text-xs">{p.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── THE CORE LOOP ───────────────────────────────────────────────────── */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-white mb-3">The Hero Journey</h2>
            <p className="text-gray-400">Every step is implemented, working, and grounded in real learner data.</p>
          </div>
          <div className="glass-card p-6 md:p-8">
            <div className="flex flex-wrap justify-center gap-2 md:gap-0">
              {CORE_LOOP.map((step, i) => (
                <div key={step.label} className="flex items-center gap-1 md:gap-2">
                  <div className="flex flex-col items-center gap-1">
                    <div className="w-10 h-10 rounded-full flex items-center justify-center text-lg"
                      style={{ background: `hsl(${220 + i * 14}, 70%, 20%)`, border: `1px solid hsl(${220 + i * 14}, 70%, 40%)` }}>
                      {step.icon}
                    </div>
                    <span className="text-xs text-gray-400 text-center whitespace-nowrap">{step.label}</span>
                  </div>
                  {i < CORE_LOOP.length - 1 && (
                    <div className="text-gray-700 text-lg mb-5 hidden md:block">↓</div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-6 pt-6 text-center" style={{ borderTop: '1px solid rgba(99,102,241,0.15)' }}>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm"
                style={{ background: 'rgba(99,102,241,0.12)', color: '#a5b4fc' }}>
                <Zap className="w-4 h-4 text-amber-400" />
                <span className="font-semibold text-amber-300">Innovation: What-If Simulator</span>
                <span className="text-gray-400">— Simulate "5h/week" or "I already know Python" before committing</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── DIFFERENTIATORS ─────────────────────────────────────────────────── */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-white mb-3">What Makes NeuraLearn Different</h2>
            <p className="text-gray-400">7 ideas that judges should remember</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {DIFFERENTIATORS.map((d, i) => (
              <motion.div
                key={d.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="glass-card-hover p-6"
              >
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${d.bg}`}>
                  <d.icon className={`w-5 h-5 bg-gradient-to-r ${d.color} bg-clip-text`} style={{ color: 'transparent', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundImage: `linear-gradient(to right, var(--tw-gradient-stops))` }} />
                  <d.icon className="w-5 h-5 text-white absolute opacity-0" />
                  <d.icon className="w-5 h-5" style={{ color: d.color.includes('rose') ? '#f43f5e' : d.color.includes('violet') ? '#8b5cf6' : d.color.includes('amber') ? '#f59e0b' : d.color.includes('emerald') ? '#10b981' : d.color.includes('cyan') ? '#06b6d4' : '#6366f1' }} />
                </div>
                <h3 className="font-bold text-white mb-0.5">{d.title}</h3>
                <p className="text-xs font-medium mb-2" style={{ color: 'var(--text-muted)' }}>{d.subtitle}</p>
                <p className="text-sm text-gray-400 leading-relaxed">{d.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── THE WOW MOMENT ─────────────────────────────────────────────────── */}
      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card p-8 md:p-12 text-center"
            style={{ borderColor: 'rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.06)' }}>
            <p className="text-sm text-indigo-400 font-semibold uppercase tracking-wide mb-4">The Demo Moment</p>
            <h2 className="text-3xl font-bold text-white mb-8">Take a quiz → watch the path change</h2>
            <div className="grid md:grid-cols-3 gap-4">
              {DEMO_FLOW.map((item, i) => (
                <div key={i} className="rounded-xl p-4" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <p className="text-xs text-gray-500 mb-2">{item.label}</p>
                  <div className="text-sm text-gray-400 mb-1 line-through">{item.before}</div>
                  <div className="text-sm text-indigo-300 font-semibold flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    {item.after}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 inline-flex items-center gap-3 px-6 py-3 rounded-2xl text-lg font-bold"
              style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.3))', border: '1px solid rgba(99,102,241,0.4)' }}>
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <span className="gradient-text">Your learning path has adapted.</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────────────────── */}
      <section className="py-20 px-6 text-center">
        <div className="max-w-xl mx-auto">
          <Brain className="w-12 h-12 mx-auto mb-4 text-indigo-400" />
          <h2 className="text-3xl font-bold text-white mb-4">Start your adaptive learning journey</h2>
          <p className="text-gray-400 mb-8">Tell NeuraLearn your goal. We'll handle the rest.</p>
          <Link to="/register" className="btn-primary inline-flex items-center gap-2 py-3 px-8 text-base">
            Build My Roadmap Free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 text-center text-xs text-gray-600"
        style={{ borderTop: '1px solid rgba(99,102,241,0.1)' }}>
        <div className="flex items-center justify-center gap-2 mb-2">
          <Brain className="w-3.5 h-3.5 text-indigo-400" />
          <span className="gradient-text font-semibold">NeuraLearn AI</span>
        </div>
        <p>PathFinder Round 2 Submission • Adaptive AI Learning Engine • Powered by Gemini 2.5</p>
      </footer>
    </div>
  )
}
