# Explainable Recommendations — Requirements

## Overview
Every skill recommendation must be grounded in actual learner data — not a generic statement.
The system must be able to answer "Why am I learning this now?" with specific numbers.

## Functional Requirements

### FR-1: Per-Skill Explanation Endpoint
- `GET /analytics/explain/{skill}` must return a human-readable explanation for why a skill
  is recommended, grounded in the learner's actual mastery data.
- The explanation must reference: current mastery %, target role, prerequisites, strong skills.
- The LLM is used only to produce the natural-language narrative — all input numbers come
  from the deterministic skill gap engine.

### FR-2: Fallback Explanation
- If the AI provider is unavailable, a deterministic fallback explanation must be returned.
- Fallback format: "Your current mastery of {skill} is {X}%, which is below the {role} target.
  {prereq note}. Improving this skill will directly increase your career readiness score."

### FR-3: Inline Explainability in Analytics Page
- The AnalyticsPage skill gap bars must have an (ℹ) icon on each skill.
- Clicking the icon fetches and displays the explanation inline below the bar.
- Only one explanation is shown at a time (clicking another skill collapses the previous).

### FR-4: Roadmap Resource Explanations
- Each resource in a milestone must display its `why_recommended` field.
- This field is AI-generated during roadmap creation and must reference the learner's
  gap context (e.g. "Docker is your largest prerequisite gap for the MLOps milestone").

### FR-5: Priority Order Explainability
- The Analytics page must show the priority learning order (1, 2, 3...) with clickable
  skill names that trigger the explanation panel.

## Non-Functional Requirements
- Explanation endpoint must handle AI timeouts gracefully and always return a response.
- Explanation text must be 2–4 sentences maximum (enforced in the prompt).

## Acceptance Criteria
- AC-1: `GET /analytics/explain/MLOps` returns explanation text that mentions the current mastery %.
- AC-2: If AI is unavailable (no API key), a valid deterministic explanation is still returned.
- AC-3: Clicking (ℹ) on a skill bar in AnalyticsPage shows an explanation with actual numbers.
- AC-4: The explanation for a "strong" skill acknowledges strength rather than recommending it.
- AC-5: Resource why_recommended fields are non-empty in generated roadmaps.
