# Learner Dashboard — Requirements

## Overview
The dashboard communicates the learner's current state, progress, and next action at a glance.
It must be immediately actionable — the learner should never ask "what should I do next?"

## Functional Requirements

### FR-1: Next Best Action Card
- The dashboard must show the highest-priority learning action derived from current skill mastery.
- Each action must include: skill name, reason (references actual mastery %), estimated hours.
- A "Take Quiz" button must pre-fill the quiz topic with the recommended skill.
- The NBA card must update automatically after quiz submissions.

### FR-2: Career Readiness Meter
- A semi-circular gauge showing career_readiness_pct (0–100).
- readiness is computed deterministically from skill mastery vs. required skills for the target role.
- Below the gauge: 3 strong skills (green) and 3 gap skills (red) as quick reference.

### FR-3: Skill Radar Chart
- Radar chart showing up to 7 skills by mastery score.
- Data source: SkillMastery table — NOT hardcoded placeholder data.
- If no mastery data exists: show empty state ("Complete onboarding to see your skill radar").

### FR-4: Roadmap Progress Chart
- Horizontal bar chart showing completion_percentage per active roadmap.
- Data source: Roadmap.completion_percentage — NOT hardcoded month labels.
- Empty state: "Generate a roadmap to track progress" with link.

### FR-5: Quick Stats
- 4 stat cards: Day Streak, Milestones (X/Y), Quiz Avg %, Career Ready %.
- All stats come from real DB aggregations — no mock data.

### FR-6: Active Roadmaps List
- List of active roadmaps with animated progress bars.
- Links to the Roadmap page.

## Non-Functional Requirements
- Dashboard must load with a single API call to `GET /analytics/dashboard`.
- NBA and skill gap are separate fetches (they have different update frequencies).
- No hardcoded placeholder data in production code paths.

## Acceptance Criteria
- AC-1: Dashboard shows "Complete your profile" state when no profile exists.
- AC-2: NBA card appears after onboarding with a real skill recommendation.
- AC-3: Skill radar shows real mastery data after onboarding.
- AC-4: Completing a milestone updates the roadmap progress bar.
- AC-5: Taking a quiz updates the Career Ready % and NBA card.
