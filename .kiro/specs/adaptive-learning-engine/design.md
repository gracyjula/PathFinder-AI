# Adaptive Learning Engine — Design

## Data Flow

```
Learner submits quiz
        │
        ▼
POST /analytics/quiz/submit
        │
        ├─► Score calculation (deterministic: correct/total × 100)
        │
        ├─► mastery_service.apply_quiz_result(user_id, topic, score)
        │       │
        │       ├─► normalize_skill(topic)  ← canonical name
        │       ├─► read existing SkillMastery row
        │       ├─► update_mastery_from_quiz(old, quiz_score, evidence_count)
        │       │       formula: Bayesian credibility blend
        │       └─► upsert SkillMastery row
        │
        ├─► if |delta| > 5:
        │       record_adaptation(trigger="quiz_result", skill, old, new, action_text)
        │
        └─► return { score, mastery_update: { skill, old_mastery, new_mastery, delta } }


Learner clicks "Adapt Roadmap"
        │
        ▼
POST /roadmap/{id}/adapt
        │
        ├─► get_mastery_map(user_id)  ← all SkillMastery rows as dict
        ├─► calculate_skill_gap(target_role, mastery_map)  ← SkillGapResult
        ├─► for each incomplete milestone:
        │       for each topic in milestone.topics:
        │           lookup topic in skill_status
        │           assign action: accelerate / reinforce / normal
        │       derive milestone adaptation_status from worst topic
        │
        ├─► store adaptation summary in roadmap.ai_generated_data
        ├─► record_adaptation(trigger="manual_adapt", ...)
        └─► return { roadmap_id, career_readiness_pct, adaptations[], summary }
```

## Mastery Update Formula

```python
def update_mastery_from_quiz(current, quiz_score, evidence_count):
    weight_new = 1.0 / (1.0 + evidence_count * 0.2)
    weight_old = 1.0 - weight_new
    return current * weight_old + quiz_score * weight_new
```

Evidence count effect on blending:
- 0 prior data points: quiz_score has 100% weight (first evidence dominates)
- 1 prior data point: quiz_score has ~83% weight
- 5 prior data points: quiz_score has ~50% weight
- 10 prior data points: quiz_score has ~33% weight (mastery is stable, hard to move)

This prevents a single outlier quiz from destroying an established mastery score.

## Frontend Components

### QuizPage — Mastery Update Banner
Appears after submission. Shows:
- Skill name
- Old mastery → New mastery with animated progress bar
- Delta value (green if positive, red if negative)
- "Your roadmap and next best actions have been updated."

### RoadmapPage — Adaptation Badges
After clicking "Adapt Roadmap":
- Each milestone shows a status badge (⚡/🔁/✅)
- Expanded milestone shows per-skill adaptation details with reason text
- Summary banner at top: "X milestones adapted"

### DashboardPage — Next Best Action
- Fetches `/analytics/next-best-action` on load
- Shows top action with skill name, reason, estimated hours
- "Take Quiz" button pre-fills the topic
