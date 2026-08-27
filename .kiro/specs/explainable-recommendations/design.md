# Explainable Recommendations — Design

## Explanation Generation Pipeline

```
GET /analytics/explain/{skill}
        │
        ├─► normalize_skill(skill)  ← canonical name
        ├─► get_mastery_map(user_id)
        ├─► current_mastery = mastery_map.get(skill, 0.0)
        ├─► get_skill_gap_for_user(user_id, target_role)
        ├─► item = find skill in gap_result.required_skills
        ├─► prerequisites = item.prerequisites
        │
        ▼
generate_skill_gap_explanation(
    skill=canonical,
    current_mastery=X,        ← real number from DB
    target_role=profile.career_goal,
    prerequisites=[...],      ← from RoleSkillGraph
    strong_skills=[...],      ← from gap_result
)
        │
        ├─► Build grounded prompt with actual numbers
        ├─► Call AI provider (Gemini → OpenAI → OpenRouter)
        │
        ├─► On success: return AI narrative (2–3 sentences)
        └─► On failure: return deterministic fallback string

Response: {
    skill, current_mastery, target_role,
    prerequisites, explanation, status, importance
}
```

## Prompt Design Principle
The prompt explicitly:
1. Provides the mastery percentage as a hard number.
2. Lists the prerequisites from the graph (not invented by AI).
3. Lists the learner's strong skills (from deterministic calculation).
4. Forbids generic statements ("this course is useful for your career").
5. Requires the explanation to reference the actual mastery number.

This ensures the AI acts as a narrator, not a decision-maker.

## Deterministic Fallback
```python
prereq_note = f" It builds on {prereq_text}." if prerequisites else ""
return (
    f"Your current mastery of {skill} is {current_mastery:.0f}%, "
    f"which is below the {target_role} target.{prereq_note} "
    f"Improving this skill will directly increase your career readiness score."
)
```

## Frontend Interaction Pattern

```
AnalyticsPage
  [Python ████████░░ 80%]  (ℹ) ← click
      ↓
  [Explanation panel slides in below bar]
  "Your Python mastery is at 80%, placing it in the Strong category for AI Engineer.
   Since Python is already strong, your focus should shift to Machine Learning,
   which builds directly on Python and is currently at 40% mastery."
  ↑ AI-generated, but all numbers are real
```

## Resource Why-Recommended
Generated during `generate_roadmap()` — the prompt includes the learner's gap context:
```
"For each resource, set why_recommended to explain why this specific learner needs it,
referencing their current skill gaps."
```
This is AI-generated narrative but shaped by real gap data passed into the prompt.
