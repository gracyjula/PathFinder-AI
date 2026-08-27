# Core Learning Flow — Requirements

## Overview
The core learning flow is the end-to-end journey from a learner stating a goal to receiving a
personalized, prerequisite-aware roadmap grounded in their actual skill mastery.

## Functional Requirements

### FR-1: Conversational Goal Intake
- The learner can describe their target role, current skills, experience level, available weekly
  hours, and target deadline in natural language via the AI Mentor chat.
- The system must extract structured data from free-form input using the AI intent analyzer.
- Extracted data must be persisted to the LearnerProfile immediately after extraction.

### FR-2: Learner Profile
- A LearnerProfile must exist for every learner before a roadmap can be generated.
- Profile fields: career_goal, experience_level, current_skills, weekly_hours,
  target_timeline_months, learning_style, interests, education.
- Profile must be the single source of truth for personalization — no duplicated state.

### FR-3: Skill Mastery Initialization
- When a profile is created or updated with new skills, SkillMastery rows must be seeded
  deterministically from the skill list and experience level.
- Self-reported "strong" → 75%, "intermediate" → 55%, "basic" → 35%.
- Seeding must NOT overwrite existing mastery rows that were built from quiz evidence.

### FR-4: Skill Gap Analysis
- The skill gap report must be computed deterministically from the RoleSkillGraph and
  current SkillMastery data — NOT from an LLM alone.
- Each required skill must carry: current_mastery (0–100), gap_score, status
  (strong/developing/gap), importance weight, prerequisites, prerequisites_met flag.
- The report must be persisted to profile.skill_gap_report as JSON.

### FR-5: Prerequisite Graph
- The system must maintain a static RoleSkillGraph with required skills per role,
  importance weights, and prerequisite relationships.
- Supported roles: AI Engineer, ML Engineer, Data Scientist, Full Stack Developer,
  Cloud Engineer, Software Engineer, Generative AI Engineer, Data Analyst.
- The roadmap generator must receive the prerequisite graph so that advanced topics are
  never recommended before foundational prerequisites are met.

### FR-6: Roadmap Generation
- Roadmaps must be generated using: career goal, current skills, experience level,
  weekly_hours, target_timeline_months, learning_style.
- Each milestone must contain: title, description, topics, resources (with why_recommended),
  projects, estimated_hours, difficulty, outcomes.
- Roadmaps must be persisted with milestones in the database.
- Completion percentage must be recalculated deterministically after each milestone is marked
  complete.

## Non-Functional Requirements
- Skill gap calculation must complete in < 50ms (pure Python, no AI call).
- Profile creation must seed mastery within the same HTTP request (single transaction).
- Roadmap generation may take up to 30s (AI call) — frontend must show a loading state.

## Acceptance Criteria
- AC-1: A new user can complete onboarding and see a generated roadmap without manual DB setup.
- AC-2: `GET /analytics/skill-gap` returns a valid SkillGapReport within 100ms for a profiled user.
- AC-3: Profile creation automatically creates SkillMastery rows for all listed skills.
- AC-4: The roadmap includes at least 3 milestones and each milestone has at least 1 resource.
- AC-5: Completing all milestones sets roadmap.completion_percentage to 100.
