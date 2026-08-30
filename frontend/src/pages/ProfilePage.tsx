import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { User, Upload, Loader2, Save, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const SKILLS_POOL = [
  'Python', 'JavaScript', 'Java', 'C++', 'SQL', 'ML', 'Deep Learning',
  'NLP', 'React', 'Node.js', 'Docker', 'AWS', 'DSA', 'System Design',
  'MongoDB', 'TensorFlow', 'PyTorch', 'Git', 'Linux', 'TypeScript',
]

// Default form values used both for new users and as fallback
const DEFAULT_FORM = {
  career_goal: '',
  education: '',
  institution: '',
  year_of_study: 1 as number | null,
  experience_level: 'beginner',
  weekly_hours: 10,
  learning_style: 'mixed',
  current_skills: [] as string[],
  interests: [] as string[],
  target_timeline_months: 12,
}

export default function ProfilePage() {
  const { profile, setProfile, user, isProfileLoading, fetchProfile } = useAuthStore()
  const qc = useQueryClient()

  // Initialise form from store profile; re-sync if the profile object changes
  // (e.g. after the initial page-load fetch completes).
  const [formData, setFormData] = useState(() => ({
    career_goal: profile?.career_goal || DEFAULT_FORM.career_goal,
    education: profile?.education || DEFAULT_FORM.education,
    institution: profile?.institution || DEFAULT_FORM.institution,
    year_of_study: profile?.year_of_study ?? DEFAULT_FORM.year_of_study,
    experience_level: profile?.experience_level || DEFAULT_FORM.experience_level,
    weekly_hours: profile?.weekly_hours ?? DEFAULT_FORM.weekly_hours,
    learning_style: profile?.learning_style || DEFAULT_FORM.learning_style,
    current_skills: profile?.current_skills ?? DEFAULT_FORM.current_skills,
    interests: profile?.interests ?? DEFAULT_FORM.interests,
    target_timeline_months: profile?.target_timeline_months ?? DEFAULT_FORM.target_timeline_months,
  }))

  // Sync form when the store profile is loaded/updated after mount
  useEffect(() => {
    if (profile) {
      setFormData({
        career_goal: profile.career_goal || '',
        education: profile.education || '',
        institution: profile.institution || '',
        year_of_study: profile.year_of_study ?? 1,
        experience_level: profile.experience_level || 'beginner',
        weekly_hours: profile.weekly_hours ?? 10,
        learning_style: profile.learning_style || 'mixed',
        current_skills: profile.current_skills ?? [],
        interests: profile.interests ?? [],
        target_timeline_months: profile.target_timeline_months ?? 12,
      })
    }
  }, [profile])

  const [resumeFile, setResumeFile] = useState<File | null>(null)

  // Whether we're still waiting for the initial profile fetch to finish.
  // isProfileLoading is set by authStore.fetchMe / fetchProfile.
  const isInitialLoading = isProfileLoading

  // ── Save / Update profile ──────────────────────────────────────────────────
  // Uses PATCH if profile already exists, POST if this is the first save.
  const updateMutation = useMutation({
    mutationFn: async () => {
      if (profile) {
        // Profile exists → update
        return api.patch('/profile', formData)
      } else {
        // No profile yet → create (handles users who skipped onboarding)
        return api.post('/profile', formData)
      }
    },
    onSuccess: async (res) => {
      setProfile(res.data)
      // Re-fetch so the store is fully in sync (triggers isProfileLoading
      // briefly but that's fine — the page is already rendered)
      try { await fetchProfile() } catch { /* ignore */ }
      qc.invalidateQueries({ queryKey: ['skill-gap-current'] })
      qc.invalidateQueries({ queryKey: ['next-best-action'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
      toast.success(profile ? 'Profile updated!' : 'Profile created!')
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail
      if (detail === 'Profile already exists. Use PATCH to update.') {
        // Race condition: profile was created between render and save.
        // Retry as PATCH.
        api.patch('/profile', formData).then(r => {
          setProfile(r.data)
          toast.success('Profile updated!')
        }).catch(() => toast.error('Update failed — please try again'))
      } else {
        toast.error(detail || 'Save failed — please try again')
      }
    },
  })

  // ── Resume upload ──────────────────────────────────────────────────────────
  const resumeMutation = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      fd.append('file', resumeFile!)
      if (formData.career_goal) fd.append('target_role', formData.career_goal)
      return api.post('/analytics/resume', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    onSuccess: (res) => {
      const extracted: string[] = res.data.extracted_skills || []
      toast.success(`Extracted ${extracted.length} skills from your resume!`)
      setFormData(d => ({
        ...d,
        current_skills: [...new Set([...d.current_skills, ...extracted])],
      }))
    },
    onError: () => toast.error('Resume analysis failed'),
  })

  const toggleSkill = (skill: string) =>
    setFormData(d => ({
      ...d,
      current_skills: d.current_skills.includes(skill)
        ? d.current_skills.filter(s => s !== skill)
        : [...d.current_skills, skill],
    }))

  // ── Loading state — only while the initial fetch is still in flight ────────
  if (isInitialLoading) {
    return (
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">My Profile</h1>
        <div className="glass-card p-10 flex flex-col items-center justify-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-primary-400" />
          <p className="text-gray-400 text-sm">Loading your profile…</p>
        </div>
      </div>
    )
  }

  // ── No profile + not loading → user skipped onboarding ────────────────────
  // Still show the form (pre-filled with defaults) so they can create one here,
  // but also offer a quick link to the proper onboarding flow.
  const isNewUser = !profile

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">My Profile</h1>

      {/* New-user banner — shown when no profile exists yet */}
      {isNewUser && (
        <div className="glass-card p-4 border border-primary-500/30 bg-primary-500/5 flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-primary-300 mb-0.5">Profile not set up yet</p>
            <p className="text-xs text-gray-400">
              Fill in the form below and click Save, or go through the full onboarding for a better experience.
            </p>
          </div>
          <Link
            to="/onboarding"
            className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5 whitespace-nowrap flex-shrink-0"
          >
            Full Onboarding <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      )}

      {/* Avatar & name */}
      <div className="glass-card p-6 flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
          {user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'}
        </div>
        <div>
          <p className="font-semibold text-white text-lg">{user?.full_name || user?.username}</p>
          <p className="text-gray-400 text-sm">{user?.email}</p>
          <p className="text-primary-400 text-sm capitalize mt-0.5">
            {formData.experience_level} • {formData.career_goal || 'No goal set'}
          </p>
        </div>
      </div>

      {/* Goal & Education */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="font-semibold text-white">Goal & Education</h2>
        <input
          value={formData.career_goal}
          onChange={e => setFormData(d => ({ ...d, career_goal: e.target.value }))}
          placeholder="Career Goal (e.g. AI Engineer)"
          className="input-field"
        />
        <div className="grid grid-cols-2 gap-3">
          <input
            value={formData.education}
            onChange={e => setFormData(d => ({ ...d, education: e.target.value }))}
            placeholder="Degree (e.g. B.Tech AIML)"
            className="input-field"
          />
          <input
            value={formData.institution}
            onChange={e => setFormData(d => ({ ...d, institution: e.target.value }))}
            placeholder="Institution"
            className="input-field"
          />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <select
            value={formData.experience_level}
            onChange={e => setFormData(d => ({ ...d, experience_level: e.target.value }))}
            className="input-field"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          <select
            value={formData.target_timeline_months}
            onChange={e => setFormData(d => ({ ...d, target_timeline_months: +e.target.value }))}
            className="input-field"
          >
            {[3, 6, 9, 12, 18, 24].map(m => (
              <option key={m} value={m}>{m} months</option>
            ))}
          </select>
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Year of Study</label>
            <input
              type="number"
              min={1}
              max={6}
              value={formData.year_of_study ?? ''}
              onChange={e =>
                setFormData(d => ({
                  ...d,
                  year_of_study: e.target.value ? +e.target.value : null,
                }))
              }
              placeholder="e.g. 2"
              className="input-field"
              aria-label="Year of study"
            />
          </div>
        </div>
      </div>

      {/* Skills */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-white mb-3">
          Current Skills{' '}
          <span className="text-gray-500 font-normal text-sm">
            ({formData.current_skills.length} selected)
          </span>
        </h2>
        <div className="flex flex-wrap gap-2">
          {SKILLS_POOL.map(skill => (
            <button
              key={skill}
              onClick={() => toggleSkill(skill)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                formData.current_skills.includes(skill)
                  ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                  : 'border-white/10 bg-white/5 text-gray-400 hover:border-primary-500/30'
              }`}
            >
              {skill}
            </button>
          ))}
        </div>
      </div>

      {/* Resume Upload */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-white mb-3 flex items-center gap-2">
          <Upload className="w-4 h-4 text-accent-400" /> Resume Analyzer
        </h2>
        <p className="text-gray-400 text-sm mb-3">
          Upload your resume to auto-extract skills and analyze fit
        </p>
        <div className="flex gap-3">
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={e => setResumeFile(e.target.files?.[0] || null)}
            className="input-field text-sm file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-primary-500/20 file:text-primary-300 file:cursor-pointer"
          />
          <button
            onClick={() => resumeMutation.mutate()}
            disabled={!resumeFile || resumeMutation.isPending}
            className="btn-primary flex items-center gap-2 whitespace-nowrap"
          >
            {resumeMutation.isPending
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Upload className="w-4 h-4" />}
            Analyze
          </button>
        </div>
        {resumeMutation.isSuccess && resumeMutation.data && (
          <p className="text-xs text-green-400 mt-2">
            ✅ Skills extracted — they've been added to your selection above.
            Click Save to persist them.
          </p>
        )}
      </div>

      {/* Learning Preferences */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="font-semibold text-white">Learning Preferences</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Learning Style</label>
            <select
              value={formData.learning_style}
              onChange={e => setFormData(d => ({ ...d, learning_style: e.target.value }))}
              className="input-field"
            >
              <option value="visual">Visual</option>
              <option value="reading">Reading</option>
              <option value="hands_on">Hands-on</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Weekly Hours</label>
            <input
              type="number"
              min={1}
              max={40}
              value={formData.weekly_hours}
              onChange={e => setFormData(d => ({ ...d, weekly_hours: +e.target.value }))}
              className="input-field"
            />
          </div>
        </div>
      </div>

      {/* Save */}
      <button
        onClick={() => updateMutation.mutate()}
        disabled={updateMutation.isPending}
        className="btn-primary w-full flex items-center justify-center gap-2 py-3"
      >
        {updateMutation.isPending
          ? <Loader2 className="w-4 h-4 animate-spin" />
          : <Save className="w-4 h-4" />}
        {isNewUser ? 'Create Profile' : 'Save Changes'}
      </button>
    </div>
  )
}
