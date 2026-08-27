# NeuraLearn AI

> An adaptive AI learning-path engine that understands where a learner is, where they want
> to go, identifies the gap between the two, determines what should be learned next, explains
> why, and continuously replans the journey based on evidence of learning.

Built for the **PathFinder Round 2 challenge**.

---

## The Problem

Generic course recommendation engines tell learners *what* to study. They don't know *why*
a particular learner needs it, *when* they're ready for it, or *whether the plan should change*
after the learner demonstrates new knowledge.

## The Solution

NeuraLearn AI implements a closed-loop adaptive learning engine:

```
GOAL → LEARNER PROFILE → REQUIRED SKILLS → CURRENT MASTERY
→ SKILL GAP → PREREQUISITES → PERSONALIZED ROADMAP
→ ASSESSMENT → UPDATED MASTERY → ADAPTIVE REPLANNING
```

Every step in this loop is implemented and working end-to-end.

---

## Key Features

| Feature | Implementation |
|---|---|
| Conversational goal intake | AI intent extraction via chat → structured profile |
| Skill gap analysis | Deterministic RoleSkillGraph (8 roles, 70+ skills, prereqs) |
| Personalized roadmap | AI-generated, prerequisite-aware, per-learner profile |
| Knowledge quiz | AI-generated questions, deterministic scoring |
| Mastery tracking | Bayesian credibility blend updated after each quiz |
| Adaptive roadmap | Per-milestone adaptation status (accelerate/reinforce/normal) |
| Explainable recommendations | Per-skill "Why this?" grounded in actual mastery % |
| Next Best Action | Deterministic: highest gap × importance, prerequisite-aware |
| What-If Simulator | Stateless scenario comparison (role/hours/timeline/skills) |
| Career Readiness Score | Weighted average across required skills vs mastery |
| Dashboard | Real-time mastery radar, roadmap progress, NBA card |
| Mock Interview | AI-generated role-specific questions |
| Resume analysis | PDF/DOCX/TXT parsing → skill extraction → profile update |

---

## Architecture

```
frontend/          React 18 + Vite + TypeScript + TailwindCSS
  src/
    pages/         DashboardPage, AnalyticsPage, RoadmapPage, QuizPage,
                   WhatIfPage, ChatPage, ProfilePage, OnboardingPage,
                   InterviewPage, LandingPage, LoginPage, RegisterPage
    components/    DashboardLayout
    store/         authStore (Zustand + persist)
    lib/           api.ts (axios + interceptors + token refresh)
    types/         Full TypeScript types for all API contracts

backend/           FastAPI + Python 3.11+
  app/
    ai/
      ai_service.py    All AI functions (Gemini → OpenAI → OpenRouter fallback)
    api/routes/
      auth.py          JWT auth (register, login, refresh, me)
      profile.py       Learner profile CRUD + mastery seeding
      roadmap.py       Roadmap CRUD + milestone completion + adapt endpoint
      analytics.py     Skill gap, quiz, career readiness, weekly plan,
                       resume analysis, mock interview, what-if simulator
      chat.py          Conversational mentor with session persistence
      admin.py         Admin stats (protected)
    services/
      skill_graph.py   RoleSkillGraph, calculate_skill_gap, mastery formulas
      mastery_service.py  SkillMastery DB operations, next best action
      roadmap_service.py  Roadmap creation, progress recalculation
    models/
      models.py        User, LearnerProfile, Roadmap, Milestone, ChatSession,
                       ChatMessage, QuizResult, ProgressLog, LearningStreak,
                       SkillMastery, AdaptationEvent
    core/
      config.py        Pydantic settings (env vars)
      security.py      JWT creation and validation
      deps.py          FastAPI dependencies (get_current_user, get_db)
```

### AI Architecture

```
User Input (natural language)
        │
        ▼
AI Provider (Gemini 1.5 Pro → OpenAI GPT-4o-mini → OpenRouter)
  Used for: intent extraction, roadmap narrative, quiz generation,
            mentor chat, skill explanation, whatif narrative
        │
        ▼  narrative only
Deterministic Engine (no AI)
  Used for: skill gap scores, mastery percentages, prerequisite validation,
            quiz scoring, progress tracking, next best action ranking,
            adaptation status, feasibility calculation
```

AI is used where *reasoning* is valuable. Math is never delegated to an LLM.

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- At least one AI API key (Gemini, OpenAI, or OpenRouter)

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in:

```env
# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite+aiosqlite:///./neuralearn.db

# JWT
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Providers (at least one required)
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key       # optional fallback
OPENROUTER_API_KEY=your-openrouter-key  # optional fallback
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173  
Backend API docs: http://localhost:8000/docs

### Docker

```bash
docker-compose up --build
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000

---

## Demo Scenario

The following scenario exercises the full adaptive learning loop:

1. Register a new account.
2. In onboarding, enter:
   - Goal: *AI Engineer*
   - Skills: *Python, Machine Learning, Statistics*
   - Experience: *Intermediate*
   - Hours/week: *8*
   - Timeline: *6 months*
3. View the Dashboard — observe the skill radar showing Python and ML with real mastery scores.
   Note the **Next Best Action** card recommending the highest-gap skill.
4. Navigate to **Analytics** — see the deterministic skill gap bars for all AI Engineer required skills.
   Click the ℹ icon on any skill to get a grounded "Why this?" explanation.
5. Navigate to **My Roadmap** — view the AI-generated prerequisite-aware roadmap.
   Click a topic chip to open its explanation panel.
6. Navigate to **Quiz** — the recommended skill should be pre-selected.
   Complete a quiz and observe the **mastery update banner** showing old → new mastery.
7. Return to **My Roadmap** — click **Adapt Roadmap**.
   Observe milestones tagged ⚡ (accelerate) or 🔁 (reinforce) based on current mastery.
8. Navigate to **What-If Simulator**:
   - Reduce hours to 5/week → Run Simulation → observe feasibility warning.
   - Add "Deep Learning" to known skills → Run Simulation → observe readiness increase.
   - Change role to ML Engineer → Run Simulation → observe changed priority skills.

---

## API Documentation

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

Key endpoints:

| Method | Path | Description |
|---|---|---|
| POST | /api/v1/auth/register | Create account |
| POST | /api/v1/auth/login | Get JWT tokens |
| GET | /api/v1/profile | Get learner profile |
| POST | /api/v1/profile | Create profile (seeds skill mastery) |
| GET | /api/v1/analytics/skill-gap | Deterministic skill gap |
| GET | /api/v1/analytics/mastery | Current skill mastery map |
| GET | /api/v1/analytics/next-best-action | Top 3 learning priorities |
| GET | /api/v1/analytics/explain/{skill} | Grounded skill explanation |
| POST | /api/v1/analytics/quiz/generate | Generate quiz for a topic |
| POST | /api/v1/analytics/quiz/submit | Score quiz + update mastery |
| POST | /api/v1/analytics/whatif | What-if simulation |
| POST | /api/v1/roadmap | Generate personalized roadmap |
| POST | /api/v1/roadmap/{id}/adapt | Adapt roadmap to current mastery |
| GET | /api/v1/analytics/dashboard | Aggregated dashboard stats |

---

## Project Structure

```
PathFinder-AI/
├── backend/
│   ├── app/
│   │   ├── ai/             AI provider abstraction + all AI functions
│   │   ├── api/routes/     FastAPI route handlers
│   │   ├── core/           Config, security, dependencies
│   │   ├── db/             Database session and connection
│   │   ├── models/         SQLAlchemy ORM models
│   │   ├── schemas/        Pydantic request/response schemas
│   │   └── services/       Business logic (skill graph, mastery, roadmap)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     Shared UI components
│   │   ├── lib/            API client
│   │   ├── pages/          Page-level React components
│   │   ├── store/          Zustand auth store
│   │   └── types/          TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
├── .kiro/
│   └── specs/              Feature specs (requirements, design, tasks)
└── docker-compose.yml
```

---

## Technical Decisions

**Why deterministic skill gap instead of pure LLM?**  
LLMs produce inconsistent scores and cannot be audited. The `skill_graph.py` engine produces
the same score for the same inputs every time, supports testing, and can be explained to the
learner with actual numbers.

**Why Bayesian mastery blending?**  
A single quiz score should not completely override accumulated evidence. The credibility
weighting formula ensures that mastery becomes more stable as more evidence accumulates,
while still allowing significant updates from strong new evidence.

**Why not rebuild from scratch?**  
The existing codebase had a solid architecture (FastAPI async, React + Vite, AI provider
abstraction). The work focused on fixing crash bugs, adding the missing deterministic layer,
wiring up the adaptive loop, and improving the UI — not rebuilding working functionality.
