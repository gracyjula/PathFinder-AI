# What-If Simulator — Requirements

## Overview
The What-If Simulator lets learners explore how changing parameters (hours, role, timeline,
known skills) would affect their learning path — without committing any changes.

## Functional Requirements

### FR-1: Simulation Parameters
- The learner can simulate changes to: weekly_hours, target_role, timeline_months, known_skills.
- known_skills is comma-separated text — skills listed are treated as "intermediate" mastery
  for simulation purposes only.
- All parameters default to the learner's current profile values.

### FR-2: Simulation Computation
- Simulation is pure computation — NO DB writes until learner confirms.
- Backend computes two SkillGapResult objects: current and simulated.
- Estimates total gap hours (gap_score × 0.5) and compares against available hours.
- Returns feasibility flag (feasible_in_timeline) and estimated_months_needed.

### FR-3: Impact Summary
- Response must include an `impact` object with:
  - readiness_change: delta in career_readiness_pct (float)
  - months_change: delta in estimated_months_needed (float)
  - explanation: AI-generated narrative (2–3 sentences, grounded in the numbers)

### FR-4: Changes List
- Response must include a human-readable `changes` list describing what was modified.
- Empty changes (no-op simulation) must be handled gracefully.

### FR-5: Simulation Label
- The simulation response must include `simulation_label: "What-If Scenario (not saved — confirm to apply)"`.
- This label must be visible in the UI to clearly communicate no changes have been saved.

### FR-6: Feasibility Warning
- If simulated.feasible_in_timeline is false, the UI must show a warning card explaining
  the gap (months needed vs. available) and suggesting corrective action.

## Non-Functional Requirements
- Simulation must complete in < 500ms (no AI call for computation; AI only for explanation narrative).
- If AI explanation fails, a deterministic fallback must be used.
- Simulation must never modify profile, mastery, or roadmap tables.

## Acceptance Criteria
- AC-1: Reducing weekly_hours from 10 to 5 increases estimated_months_needed.
- AC-2: Adding a known skill to the simulation increases career_readiness_pct.
- AC-3: Changing target_role changes the required skills and priority list.
- AC-4: The UI shows "What-If Scenario (not saved)" label prominently.
- AC-5: A feasibility warning appears when estimated_months_needed > timeline_months.
- AC-6: Simulation response is returned even when AI explanation times out (fallback used).
