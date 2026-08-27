# Learner Dashboard — Design

## Data Sources Per Component

| Component              | API Endpoint                    | Update Trigger              |
|------------------------|---------------------------------|-----------------------------|
| Quick Stats            | GET /analytics/dashboard        | Page load                   |
| Career Readiness meter | GET /analytics/skill-gap        | Profile update, quiz submit |
| Skill Radar            | GET /analytics/mastery          | Profile create, quiz submit |
| Roadmap Progress bars  | GET /analytics/dashboard        | Milestone complete          |
| Next Best Action       | GET /analytics/next-best-action | Quiz submit, profile update |

## Query Invalidation Strategy (React Query)

After quiz submit:
  invalidate: ['mastery', 'skill-gap-current', 'next-best-action', 'dashboard']

After milestone complete:
  invalidate: ['roadmaps', 'dashboard', 'next-best-action']

After profile update:
  invalidate: ['mastery', 'skill-gap-current', 'next-best-action', 'dashboard']

## NBA Card Logic (backend)

```python
get_next_best_actions(gap_result, mastery_map, weekly_hours):
    1. For each required skill (sorted by gap × importance):
       a. If status == "strong": skip
       b. If prerequisites not met: recommend the prerequisite first (priority × 1.2)
       c. Otherwise: recommend the skill directly
    2. Deduplicate
    3. Return top 3
```

The "Take Quiz" button on the NBA card uses React Router `location.state`:
```tsx
<Link to="/dashboard/quiz" state={{ prefillTopic: topNba.skill }}>
  Take Quiz
</Link>
```
QuizPage reads `location.state?.prefillTopic` and pre-selects the topic.

## Empty States
- No profile: "Complete your profile to get started" with link to onboarding
- No mastery data: show empty radar placeholder (not random data)
- No roadmap: "Generate a roadmap to track progress" with generate link
- No NBA: hidden (only shown when profile has career_goal)

## Layout
```
┌─────────────────────────────────────────────┐
│  Welcome back, [Name] 👋                    │
│  You're on track to become a [career_goal]  │
├─────────────────────────────────────────────┤
│  [NBA Card - full width]                    │
│  🎯 Focus on: MLOps  ~5h  [Take Quiz →]    │
│  "Your MLOps mastery is 10%..."             │
├──────────┬──────────────┬───────────────────┤
│ 4 Stats  │ 4 Stats      │ 4 Stats  4 Stats  │
├──────────┴──────────────┴───────────────────┤
│ Readiness │ Skill Radar │ Roadmap Progress  │
│  Gauge   │   Radar     │   Bar Chart       │
├─────────────────────────────────────────────┤
│  Active Roadmaps (progress bars)            │
├──────────┬──────────┬───────────────────────┤
│ AI Mentor│ Roadmap  │ Quiz  │ What-If       │
└──────────┴──────────┴───────┴───────────────┘
```
