// NeuraLearn AI - TypeScript Type Definitions

export interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  avatar_url: string | null
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface LearnerProfile {
  id: string
  user_id: string
  education: string | null
  degree: string | null
  year_of_study: number | null
  institution: string | null
  career_goal: string | null
  learning_goal: string | null
  target_timeline_months: number | null
  current_skills: string[]
  completed_courses: string[]
  interests: string[]
  experience_level: string
  learning_style: string
  weekly_hours: number | null
  preferred_difficulty: string
  preferred_languages: string[]
  career_readiness_score: number | null
  skill_gap_report: SkillGapReport | null
  created_at: string
  updated_at: string
}

export interface SkillGapReport {
  target_role: string
  required_skills: string[]
  current_skills: string[]
  missing_skills: string[]
  gap_percentage: number
  skill_scores: Record<string, number>
  recommendations: string[]
  priority_skills?: string[]
  estimated_months_to_close_gap?: number
}

export interface Milestone {
  id: string
  month_number: number
  title: string
  description: string | null
  topics: string[]
  resources: Resource[]
  projects: Project[]
  estimated_hours: number | null
  difficulty: 'beginner' | 'intermediate' | 'advanced'
  is_completed: boolean
  completed_at: string | null
  outcomes: string[]
}

export interface Resource {
  title: string
  url: string
  type: string
  provider: string
  is_free: boolean
  duration_hours: number
  why_recommended: string
}

export interface Project {
  title: string
  description: string
  difficulty: string
  skills_practiced: string[]
}

export interface Roadmap {
  id: string
  user_id: string
  title: string
  goal: string
  description: string | null
  status: 'active' | 'completed' | 'paused'
  total_months: number
  completion_percentage: number
  milestones: Milestone[]
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  metadata: Record<string, any> | null
  created_at: string
}

export interface ChatSession {
  id: string
  title: string | null
  session_type: string
  messages: ChatMessage[]
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface DashboardStats {
  profile: {
    career_goal: string | null
    career_readiness_score: number
    current_skills: string[]
    experience_level: string
  }
  roadmaps: Array<{
    id: string
    title: string
    completion_percentage: number
  }>
  streak: {
    current_streak: number
    longest_streak: number
    total_days_active: number
  }
  milestones: {
    total: number
    completed: number
    percentage: number
  }
  quizzes: {
    count: number
    avg_score: number
  }
}

export interface CareerReadiness {
  score: number
  breakdown: Record<string, number>
  weak_areas: string[]
  strong_areas: string[]
  suggestions: string[]
  interview_ready: boolean
  estimated_months_to_ready: number
}

export interface WeeklyPlan {
  week_number: number
  goal: string
  total_hours: number
  focus_topics: string[]
  daily_plans: Array<{
    day: string
    tasks: Array<{
      title: string
      type: string
      duration_minutes: number
      resource: string
      description: string
    }>
    total_minutes: number
  }>
  revision_slots: string[]
  assessment: string
}

export interface Quiz {
  topic: string
  difficulty: string
  questions: QuizQuestion[]
}

export interface QuizQuestion {
  id: string
  question: string
  type: string
  options: string[]
  correct_answer: string
  explanation: string
}

export interface MockInterview {
  role: string
  sections: Array<{
    category: string
    questions: Array<{
      question: string
      type: string
      expected_topics: string[]
      difficulty: string
      sample_answer: string
    }>
  }>
  tips: string[]
}
