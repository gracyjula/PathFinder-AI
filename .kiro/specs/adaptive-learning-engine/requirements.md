# Adaptive Learning Engine — Requirements

## Overview
The adaptive learning engine updates skill mastery in response to assessment evidence and
adjusts the learner's roadmap accordingly. This is the core differentiator of NeuraLearn.

## Functional Requirements

### FR-1: Post-Quiz Mastery Update
- After every quiz submission, the relevant skill's mastery score must be updated
  deterministically using a credibility-weighted Bayesian blend.
- Formula: new = old × weight_old + quiz_score × weight_new
  where weight_new = 1 / (1 + evidence_count × 0.2)
- The quiz endpoint must return the mastery_update field:
  { skill, old_mastery, new_mastery, delta }

### FR-2: Adaptation Event Recording
- Every mastery change > 5 points must generate an AdaptationEvent row.
- Fields: trigger, skill, old_mastery, new_mastery, action_taken (human-readable).
- Events are used for the audit trail and "roadmap was adapted" UI notifications.

### FR-3: Roadmap Adaptation
- `POST /roadmap/{id}/adapt` must re-analyze all incomplete milestones using current mastery.
- Each milestone must receive an adaptation_status: accelerate / reinforce / normal.
  - accelerate: all topics are "strong" (≥ 70%) — learner can skim
  - reinforce: at least one topic is "gap" (< 35%) — learner needs extra focus
  - normal: topics are "developing" — follow plan as-is
- Adaptation must be stored in roadmap.ai_generated_data["last_adaptation"].
- The endpoint must return adaptation details per milestone for the UI to render badges.

### FR-4: Skill Status Thresholds
- strong: mastery ≥ 70
- developing: mastery 35–69
- gap: mastery < 35

### FR-5: Frontend Visibility
- The QuizPage must show the mastery_update banner after submission with old/new/delta values.
- The RoadmapPage must show adaptation badges (⚡ accelerate / 🔁 reinforce / ✅ normal)
  after the user clicks "Adapt Roadmap".
- Dashboard Next Best Action must update after any mastery change.

## Non-Functional Requirements
- Mastery update must be deterministic — no LLM involvement.
- The full quiz-submit + mastery-update cycle must complete in a single DB transaction.
- Adaptation analysis must complete in < 200ms (no AI call required).

## Acceptance Criteria
- AC-1: Submitting a quiz with score 90% increases the relevant skill's mastery score.
- AC-2: Submitting a quiz with score 10% on a skill at 50% mastery decreases it.
- AC-3: An AdaptationEvent row is created when mastery changes by > 5 points.
- AC-4: `POST /roadmap/{id}/adapt` returns adaptation_status for each incomplete milestone.
- AC-5: The QuizPage UI shows old_mastery → new_mastery with delta after submission.
- AC-6: Dashboard `/analytics/next-best-action` changes after a significant mastery update.
