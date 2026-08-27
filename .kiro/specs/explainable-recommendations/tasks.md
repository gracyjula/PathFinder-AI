# Explainable Recommendations — Tasks

## Status: COMPLETE ✅

## Completed Tasks

- [x] T-1: Add `generate_skill_gap_explanation` to `ai_service.py` with grounded prompt + deterministic fallback
- [x] T-2: Add `GET /analytics/explain/{skill}` endpoint — reads real mastery, calls AI for narrative
- [x] T-3: Frontend AnalyticsPage — (ℹ) icon on each skill bar; inline explanation panel
- [x] T-4: Frontend AnalyticsPage — priority skills list with clickable names opening explanation
- [x] T-5: Frontend RoadmapPage — topic chips are clickable and open explanation panel
- [x] T-6: Frontend RoadmapPage — resource `why_recommended` field rendered with 💡 icon

## Verification
1. Create a profile with MLOps not in known skills (mastery = 0).
2. `GET /analytics/explain/MLOps`
   Expected response.explanation contains "0%" or "beginner" and mentions Docker as prerequisite.
3. Set GEMINI_API_KEY="" and repeat.
   Expected: deterministic fallback returned (no crash).
