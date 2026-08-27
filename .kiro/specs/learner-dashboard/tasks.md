# Learner Dashboard — Tasks

## Status: COMPLETE ✅

## Completed Tasks

- [x] T-1: Add `GET /analytics/next-best-action` endpoint using deterministic skill gap
- [x] T-2: Add `GET /analytics/mastery` endpoint returning { mastery: Record<string, number> }
- [x] T-3: Fix dashboard endpoint to parse current_skills from JSON string before returning
- [x] T-4: Frontend DashboardPage — fetch /analytics/next-best-action and render NBA card
- [x] T-5: Frontend DashboardPage — "Take Quiz" CTA on NBA card with topic pre-fill via router state
- [x] T-6: Frontend DashboardPage — replace hardcoded radar data with real mastery from /analytics/mastery
- [x] T-7: Frontend DashboardPage — replace hardcoded month progress chart with real roadmap bar chart
- [x] T-8: Frontend DashboardPage — add empty states for no-mastery-data and no-roadmap cases
- [x] T-9: Frontend QuizPage — read prefillTopic from location.state
- [x] T-10: Add React Query invalidation after quiz submit (mastery, skill-gap-current, next-best-action, dashboard)

## Verification
1. Register new user → complete onboarding with Python + ML as skills.
2. Dashboard should show NBA card recommending next gap skill (e.g. Deep Learning).
3. Skill radar should show Python and Machine Learning with non-zero values.
4. Take a quiz on the recommended skill → submit.
5. Dashboard NBA card should update to reflect the new mastery.
