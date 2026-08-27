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

export interface SkillGapItem {
  skill: string
  current_mastery: number     // 0–100
  gap_score: number           // 0–100
  status: 'strong' | 'developing' | 'gap'
  importance: number          // 0–1
  prerequisites: string[]
  prerequisites_met: boolean
}

export interface SkillGapReport {
  target_role: string
  required_skills: SkillGapItem[]
  overall_gap_pct: number
  career_readiness_pct: number
  priority_skills: string[]
  strong_skills: string[]
  developing_skills: string[]
  gap_skills: string[]
  // legacy compat fields
  skill_scores: Record<string, number>
  gap_percentage: number
  missing_skills: string[]
  recommendations: string[]
  current_skills?: string[]
}

export interface MasteryMap {
  mastery: Record<string, number>
}

export interface NextBestAction {
  skill: string
  reason: string
  priority: number
  estimated_hours: number
  type: 'skill_gap' | 'prerequisite'
}

export interface SkillExplanation {
  skill: string
  current_mastery: number
  target_role: string
  prerequisites: string[]
  explanation: string
  status: string
  importance: number
}

export interface WhatIfResult {
  simulation_label: string
  changes: string[]
  current: WhatIfScenario
  simulated: WhatIfScenario
  impact: {
    readiness_change: number
    months_change: number
    explanation: string
  }
}

export interface WhatIfScenario {
  role: string
  weekly_hours: number
  timeline_months: number
  career_readiness_pct: number
  gap_skills: string[]
  priority_skills: string[]
  total_available_hours: number
  estimated_gap_hours: number
  feasible_in_timeline: boolean
  estimated_months_needed: number
}

export interface AdaptationResult {
  roadmap_id: string
  career_readiness_pct: number
  adaptations: MilestoneAdaptation[]
  summary: string
}

export interface MilestoneAdaptation {
  milestone_id: string
  milestone_title: string
  month_number: number
  adaptation_status: 'accelerate' | 'reinforce' | 'normal'
  skill_adaptations: SkillAdaptation[]
}

export interface SkillAdaptation {
  skill: string
  action: 'accelerate' | 'reinforce' | 'normal'
  reason: string
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

export interface QuizResult {
  score: number
  correct: number
  total: number
  feedback: string[]
  passed: boolean
  mastery_update: {
    skill: string
    old_mastery: number
    new_mastery: number
    delta: number
  }
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
