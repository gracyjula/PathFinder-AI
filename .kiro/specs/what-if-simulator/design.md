# What-If Simulator — Design

## Computation Pipeline

```
POST /analytics/whatif?weekly_hours=5&target_role=ML+Engineer&timeline_months=6

        │
        ├─► Load learner profile (current role, hours, timeline)
        ├─► get_mastery_map(user_id)  ← current DB mastery
        │
        ├─► Merge known_skills (comma-separated) into sim_mastery
        │     only adds skills not already in mastery, at 55% (intermediate)
        │     does NOT modify DB mastery
        │
        ├─► current_gap = calculate_skill_gap(current_role, current_mastery)
        ├─► sim_gap    = calculate_skill_gap(sim_role,     sim_mastery)
        │
        ├─► estimate_hours(skill_items, hours_per_week, timeline_months):
        │     total_available = hours_per_week * timeline * 4
        │     total_gap_hours = sum(item.gap_score * 0.5 for item in skill_items
        │                          if item.status != "strong")
        │     feasible = total_available >= total_gap_hours
        │     months_needed = total_gap_hours / (hours_per_week * 4)
        │
        ├─► Build changes[] list (human-readable diffs)
        │
        ├─► generate_whatif_explanation(original, new, changes)  ← AI narrative
        │     fallback: deterministic string if AI fails
        │
        └─► Return WhatIfResult (no DB writes)
```

## WhatIfResult Schema

```typescript
{
  simulation_label: string    // "What-If Scenario (not saved — confirm to apply)"
  changes: string[]           // ["Study time: 10h/week → 5h/week (fewer hours)", ...]
  current: WhatIfScenario
  simulated: WhatIfScenario
  impact: {
    readiness_change: number  // simulated - current career_readiness_pct
    months_change: number     // simulated - current estimated_months_needed
    explanation: string       // AI narrative or deterministic fallback
  }
}

WhatIfScenario: {
  role, weekly_hours, timeline_months,
  career_readiness_pct,
  gap_skills[], priority_skills[],
  total_available_hours,
  estimated_gap_hours,
  feasible_in_timeline,
  estimated_months_needed
}
```

## Frontend Design

```
┌─ Controls (left 2/5) ────────────────────────────┐
│  Target Role     [dropdown]                       │
│  Weekly Hours    [slider 1–40h]  Current: 8h     │
│  Timeline        [slider 3–24mo] Current: 12mo   │
│  "I already know…" [text input]                   │
│  [Run Simulation]                                 │
│                                                   │
│  Current Settings (reference card)               │
└──────────────────────────────────────────────────┘

┌─ Results (right 3/5) ────────────────────────────┐
│  "What-If Scenario (not saved)"                  │
│  • Study time: 10h/week → 5h/week                │
│                                                   │
│  [Readiness +5%] [Time: 14mo] [Feasible: No ⚠️]  │
│                                                   │
│  AI Analysis (2–3 sentences)                     │
│                                                   │
│  Scenario Comparison table                       │
│  Current | Simulated (highlighted if changed)    │
│                                                   │
│  Priority Skills (current vs simulated)          │
│  New skills highlighted in accent color          │
│                                                   │
│  ⚠️ Feasibility warning (if not feasible)         │
└──────────────────────────────────────────────────┘
```

## Key Design Decisions

1. **No DB writes during simulation** — the entire computation is stateless.
2. **known_skills only boosted if below current mastery** — prevents simulation from
   "downgrading" a skill the learner has already proven via quizzes.
3. **AI is narrative-only** — all numbers in the comparison come from deterministic computation.
4. **Sliders trigger manual run** — simulation doesn't auto-fire on every slider change
   to avoid excessive API calls. User explicitly clicks "Run Simulation".
