# Core Learning Flow — Design

## Architecture

```
Learner Input (chat / onboarding)
        │
        ▼
  AI Intent Analyzer  ──────────────────────────────────┐
  (ai_service.py)                                        │
        │ extracted_goal, current_skills,                │
        │ experience_level, timeline_months              │
        ▼                                                │
  LearnerProfile (DB)                                    │
        │                                                │
        ▼                                                │
  Mastery Seeder                                         │
  (mastery_service.initialize_mastery_from_profile)      │
        │ creates SkillMastery rows (deterministic)      │
        ▼                                                │
  RoleSkillGraph                                         │
  (skill_graph.py)                                       │
        │ required skills, importance, prerequisites     │
        ▼                                                │
  Skill Gap Engine                                       │
  (skill_graph.calculate_skill_gap)                      │
        │ SkillGapResult (pure Python, no AI)            │
        ▼                                                │
  Roadmap Generator ◄─────────────────────────────────── ┘
  (ai_service.generate_roadmap)
  feeds: gap result + profile + mastery
        │
        ▼
  Roadmap + Milestones (DB)
```

## Key Data Models

### SkillMastery
```
user_id       FK → users.id
skill         canonical skill name (normalized)
mastery_score 0–100 float
evidence_count number of quiz/assessment data points
last_assessed_at datetime
```

### RoleSkillGraph (in-memory, skill_graph.py)
```python
ROLE_SKILL_GRAPH: dict[str, list[SkillNode]]

@dataclass
class SkillNode:
    name: str
    importance: float       # 0–1
    prerequisites: list[str]
    description: str
```

### SkillGapResult (computed, not persisted directly)
```python
@dataclass
class SkillGapResult:
    target_role: str
    required_skills: list[SkillGapItem]
    overall_gap_pct: float
    career_readiness_pct: float
    priority_skills: list[str]      # sorted by gap×importance desc
    strong_skills: list[str]
    developing_skills: list[str]
    gap_skills: list[str]
```

## API Contracts

### POST /profile
Request: ProfileCreate schema
Response: ProfileOut
Side effect: seeds SkillMastery rows for all listed skills

### GET /analytics/skill-gap
Response: SkillGapReport dict
Computation: reads SkillMastery rows → calculate_skill_gap() → returns JSON

### POST /roadmap
Request: { goal, target_timeline_months }
Response: RoadmapOut with milestones
Side effect: persists Roadmap + Milestone rows

## Normalization
All user-provided skill names are normalized through `normalize_skill()` before storage and lookup.
This maps "ml" → "Machine Learning", "genai" → "Generative AI", etc.
