import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { User, Upload, Loader2, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

const SKILLS_POOL = [
  'Python', 'JavaScript', 'Java', 'C++', 'SQL', 'ML', 'Deep Learning',
  'NLP', 'React', 'Node.js', 'Docker', 'AWS', 'DSA', 'System Design',
  'MongoDB', 'TensorFlow', 'PyTorch', 'Git', 'Linux', 'TypeScript',
]

export default function ProfilePage() {
  const { profile, setProfile, user } = useAuthStore()
  const qc = useQueryClient()
  const [formData, setFormData] = useState({
    career_goal: profile?.career_goal || '',
    education: profile?.education || '',
    institution: profile?.institution || '',
    year_of_study: profile?.year_of_study || 1,
    experience_level: profile?.experience_level || 'beginner',
    weekly_hours: profile?.weekly_hours || 10,
    learning_style: profile?.learning_style || 'mixed',
    current_skills: profile?.current_skills || [],
    interests: profile?.interests || [],
    target_timeline_months: profile?.target_timeline_months || 12,
  })
  const [resumeFile, setResumeFile] = useState<File | null>(null)

  const updateMutation = useMutation({
    mutationFn: () => api.patch('/profile', formData),
    onSuccess: (res) => {
      setProfile(res.data)
      toast.success('Profile updated!')
    },
    onError: () => toast.error('Update failed'),
  })

  const resumeMutation = useMutation({
    mutationFn: () => {
      const fd = new FormData()
      fd.append('file', resumeFile!)
      if (formData.career_goal) fd.append('target_role', formData.career_goal)
      return api.post('/analytics/resume', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    },
    onSuccess: (res) => {
      toast.success(`Extracted ${res.data.extracted_skills?.length || 0} skills from your resume!`)
      setFormData(d => ({ ...d, current_skills: [...new Set([...d.current_skills, ...(res.data.extracted_skills || [])])] }))
    },
    onError: () => toast.error('Resume analysis failed'),
  })

  const toggleSkill = (skill: string) => {
    setFormData(d => ({
      ...d,
      current_skills: d.current_skills.includes(skill)
        ? d.current_skills.filter(s => s !== skill)
        : [...d.current_skills, skill],
    }))
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">My Profile</h1>

      {/* Avatar & name */}
      <div className="glass-card p-6 flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
          {user?.full_name?.[0]?.toUpperCase() || user?.username?.[0]?.toUpperCase() || 'U'}
        </div>
        <div>
          <p className="font-semibold text-white text-lg">{user?.full_name || user?.username}</p>
          <p className="text-gray-400 text-sm">{user?.email}</p>
          <p className="text-primary-400 text-sm capitalize mt-0.5">{formData.experience_level} • {formData.career_goal || 'No goal set'}</p>
        </div>
      </div>

      {/* Goal & Education */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="font-semibold text-white">Goal & Education</h2>
        <input value={formData.career_goal} onChange={e => setFormData(d => ({ ...d, career_goal: e.target.value }))}
          placeholder="Career Goal (e.g. AI Engineer)" className="input-field" />
        <div className="grid grid-cols-2 gap-3">
          <input value={formData.education} onChange={e => setFormData(d => ({ ...d, education: e.target.value }))}
            placeholder="Degree (e.g. B.Tech AIML)" className="input-field" />
          <input value={formData.institution} onChange={e => setFormData(d => ({ ...d, institution: e.target.value }))}
            placeholder="Institution" className="input-field" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <select value={formData.experience_level} onChange={e => setFormData(d => ({ ...d, experience_level: e.target.value }))}
            className="input-field">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          <select value={formData.target_timeline_months} onChange={e => setFormData(d => ({ ...d, target_timeline_months: +e.target.value }))}
            className="input-field">
            {[3, 6, 9, 12, 18, 24].map(m => <option key={m} value={m}>{m} months</option>)}
          </select>
        </div>
      </div>

      {/* Skills */}
      <div className="glass-card p-6">
        <h2 className="font-semibold text-white mb-3">Current Skills <span className="text-gray-500 font-normal text-sm">({formData.current_skills.length} selected)</span></h2>
        <div className="flex flex-wrap gap-2">
          {SKILLS_POOL.map(skill => (
            <button key={skill} onClick={() => toggleSkill(skill)}
              className={`px-3 py-1.5 rounded-full text-sm border transition-all ${
                formData.current_skills.includes(skill)
                  ? 'border-primary-500 bg-primary-500/20 text-primary-300'
                  : 'border-white/10 bg-white/5 text-gray-400 hover:border-primary-500/30'
              }`}>
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
        <p className="text-gray-400 text-sm mb-3">Upload your resume to auto-extract skills and analyze fit</p>
        <div className="flex gap-3">
          <input type="file" accept=".pdf,.docx,.txt" onChange={e => setResumeFile(e.target.files?.[0] || null)}
            className="input-field text-sm file:mr-3 file:py-1 file:px-3 file:rounded-lg file:border-0 file:bg-primary-500/20 file:text-primary-300 file:cursor-pointer" />
          <button onClick={() => resumeMutation.mutate()} disabled={!resumeFile || resumeMutation.isPending}
            className="btn-primary flex items-center gap-2 whitespace-nowrap">
            {resumeMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            Analyze
          </button>
        </div>
      </div>

      {/* Learning Preferences */}
      <div className="glass-card p-6 space-y-4">
        <h2 className="font-semibold text-white">Learning Preferences</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Learning Style</label>
            <select value={formData.learning_style} onChange={e => setFormData(d => ({ ...d, learning_style: e.target.value }))}
              className="input-field">
              <option value="visual">Visual</option>
              <option value="reading">Reading</option>
              <option value="hands_on">Hands-on</option>
              <option value="mixed">Mixed</option>
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-400 mb-1.5 block">Weekly Hours</label>
            <input type="number" min={1} max={40} value={formData.weekly_hours}
              onChange={e => setFormData(d => ({ ...d, weekly_hours: +e.target.value }))}
              className="input-field" />
          </div>
        </div>
      </div>

      {/* Save */}
      <button onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}
        className="btn-primary w-full flex items-center justify-center gap-2 py-3">
        {updateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
        Save Changes
      </button>
    </div>
  )
}
