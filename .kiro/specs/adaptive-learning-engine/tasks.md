# Adaptive Learning Engine — Tasks

## Status: COMPLETE ✅

## Completed Tasks

- [x] T-1: Add `update_mastery_from_quiz` to `skill_graph.py` (Bayesian blend, deterministic)
- [x] T-2: Add `apply_quiz_result` to `mastery_service.py` — reads existing row, blends, upserts
- [x] T-3: Update `POST /analytics/quiz/submit` to call `apply_quiz_result` after scoring
- [x] T-4: Return `mastery_update: { skill, old_mastery, new_mastery, delta }` from quiz submit
- [x] T-5: Record `AdaptationEvent` when mastery delta > 5 points
- [x] T-6: Implement `POST /roadmap/{id}/adapt` — per-milestone status analysis
- [x] T-7: Implement `GET /roadmap/{id}/adaptation-history` — event log
- [x] T-8: Frontend QuizPage — mastery update banner with animated bar and delta indicator
- [x] T-9: Frontend RoadmapPage — "Adapt Roadmap" button + adaptation status badges per milestone
- [x] T-10: Frontend RoadmapPage — per-skill adaptation detail rows in expanded milestone
- [x] T-11: Frontend DashboardPage — Next Best Action card with "Take Quiz" CTA

## Verification
1. Generate a quiz on "MLOps" — submit with all wrong answers.
   Expected: mastery_update.delta < 0 in response.
2. Submit same quiz with all correct answers.
   Expected: mastery_update.delta > 0 and new_mastery > old_mastery.
3. Click "Adapt Roadmap" on roadmap page.
   Expected: milestones with MLOps topic show "🔁 Needs Reinforcement" badge.
