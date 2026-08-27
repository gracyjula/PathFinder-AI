# What-If Simulator — Tasks

## Status: COMPLETE ✅

## Completed Tasks

- [x] T-1: Add `POST /analytics/whatif` endpoint with query params (weekly_hours, target_role, timeline_months, known_skills)
- [x] T-2: Implement stateless `estimate_hours(skill_items, hours_per_week, timeline_months)` helper
- [x] T-3: Compute current and simulated SkillGapResult and compare
- [x] T-4: Add `generate_whatif_explanation` to ai_service.py with deterministic fallback
- [x] T-5: Frontend WhatIfPage — target role dropdown, weekly hours slider, timeline slider, known skills input
- [x] T-6: Frontend WhatIfPage — 3 impact cards (readiness change, time to complete, feasibility)
- [x] T-7: Frontend WhatIfPage — scenario comparison table (current vs simulated, changed values highlighted)
- [x] T-8: Frontend WhatIfPage — priority skills comparison (new skills in accent color)
- [x] T-9: Frontend WhatIfPage — feasibility warning card when estimated_months > timeline
- [x] T-10: Wire "What-If Simulator" into DashboardLayout sidebar nav and quick actions grid
- [x] T-11: Route added to App.tsx: /dashboard/whatif → WhatIfPage

## Verification
1. Set weekly_hours=5, timeline_months=4 for an AI Engineer role.
   Expected: feasible_in_timeline=false, warning card appears.
2. Add "Python, Machine Learning, Statistics" to known_skills.
   Expected: career_readiness_pct increases vs current.
3. Change role to "Data Analyst".
   Expected: priority_skills changes (SQL and Data Analysis should appear).
4. Block AI key (set to empty string) and run simulation.
   Expected: explanation field returns deterministic fallback, simulation still works.
