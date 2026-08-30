# NeuraLearn AI

> **An adaptive AI learning-path engine that understands where a learner is, where they want to go, identifies the gap between the two, determines what should be learned next, explains why, and continuously replans the journey based on evidence of learning.**

**PathFinder Ai** — BVRITH HCL Hackathon 2026

---

## The Problem

Learning resources are abundant. Sequencing and personalization are not.

Course recommenders tell learners *what* to study. They don't know *why* that learner needs it, *whether they're ready for it*, or *how the plan should change* after the learner demonstrates new knowledge.

## The Solution

NeuraLearn implements the complete adaptive learning loop:

```
GOAL → PROFILE → SKILL ASSESSMENT → SKILL GAP → PREREQUISITE GRAPH
  → PERSONALIZED ROADMAP → RESOURCE → ASSESSMENT → MASTERY UPDATE
    → ROADMAP ADAPTATION → NEXT BEST ACTION → (repeat)
```

Every step is implemented, working, and grounded in real learner data — not AI guesses.

---

## Seven Differentiators

| # | Feature | How |
|---|---------|-----|
| 1 | **Skill-Gap First** | Required skills vs. mastery before recommending anything |
| 2 | **Prerequisite-Aware** | Structured graph — never recommends Deep Learning before ML basics |
| 3 | **Explainable** | Every recommendation has a grounded "Why this?" with actual mastery % |
| 4 | **Adaptive** | Roadmap visibly changes after quiz evidence updates mastery |
| 5 | **Evidence-Based** | Bayesian mastery blending — quiz results drive scores, not self-reports |
| 6 | **Next Best Action** | Always shows exactly what to do next and why |
| 7 | **What-If Simulator** | Simulate 5h/wk vs 10h/wk, or "I already know Python" — before committing |

---

## Architecture

```
Frontend (React + Vite + TypeScript + TailwindCSS + Zustand + Recharts + Framer Motion)
    │
    ▼ REST API
Backend (FastAPI + Python + SQLAlchemy + SQLite/PostgreSQL)
    │
    ├─ Deterministic Layer (skill_graph.py, mastery_service.py)
    │    No AI involved. Pure Python. Fully testable.
    │    - RoleSkillGraph: 11 roles, 70+ skills, prerequisites
    │    - Bayesian mastery update formula
    │    - Gap = required skills − learner mastery
    │    - Next Best Action ranking
    │
    └─ AI Layer (ai_service.py)
         Used only for: natural language, narrative explanations, roadmap text
         Provider chain: Gemini 2.5 Flash → OpenAI → OpenRouter
         Every AI call has a deterministic fallback
```

### AI/ML Architecture

```
User input (natural language)
    │
    ▼
AI: intent extraction, goal understanding, roadmap narrative generation
    │
    ▼
Deterministic: skill gap scores, mastery percentages, prerequisite validation,
               quiz scoring, progress tracking, next-best-action ranking
    │
    ▼
AI: personalized explanation ("Why this?"), adaptation narrative, what-if summary
```

**Rule:** AI is used where *reasoning* adds value. Math is never delegated to an LLM.

---

## Features

- **Conversational Goal Intake** — AI extracts structured profile from natural language
- **Learner Profile** — single canonical source: goal, skills, mastery, preferences, history
- **Skill Gap Analysis** — deterministic per-skill mastery bars (Strong/Developing/Gap)
- **Prerequisite Graph** — 11 roles × 70+ skills with dependency chains
- **Personalized Roadmap** — AI-generated, prerequisite-aware, per-learner
- **Explainable Recommendations** — `GET /analytics/explain/{skill}` with real mastery data
- **Adaptive Engine** — Quiz → mastery update → adaptation event → "Path Updated" banner
- **Quiz System** — AI-generated, deterministic scoring, mastery feedback
- **Next Best Action** — priority-ranked by gap × importance, shown on dashboard
- **What-If Simulator** — stateless scenario comparison, never modifies actual roadmap
- **Career Readiness Score** — weighted mastery average against role requirements
- **AI Mentor Chat** — contextual: knows your mastery, goal, active milestone
- **Mock Interview** — role-specific AI-generated questions
- **Resume Analysis** — PDF/DOCX/TXT → skill extraction → profile update
- **Weekly Study Plan** — AI-generated based on current milestone and weekly hours
- **Light/Dark Mode** — CSS variable system, persisted per user
- **Demo Seed** — one-click canonical demo persona for judging

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- At least one AI API key (Gemini recommended)

### 1. Clone and configure

```bash
git clone https://github.com/gracyjula/PathFinder-AI.git
cd PathFinder-AI

# Backend config
cp backend/.env.example backend/.env
# Edit backend/.env — add your GEMINI_API_KEY at minimum
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### 4. Docker (full stack with PostgreSQL)

```bash
# Add your AI keys to backend/.env first
docker-compose up --build
```

Frontend: http://localhost  
Backend: http://localhost:8000

---

## Environment Variables

```env
# backend/.env

# Database (SQLite for dev — no setup needed)
DATABASE_URL=sqlite+aiosqlite:///./neuralearn.db

# JWT
SECRET_KEY=your-secret-key-min-32-chars

# AI Providers (at least one required)
GEMINI_API_KEY=your-gemini-api-key        # Recommended: Gemini 2.5 Flash
OPENAI_API_KEY=your-openai-key            # Optional fallback
OPENROUTER_API_KEY=your-openrouter-key    # Optional fallback

# App
FRONTEND_URL=http://localhost:5173
```

---

## Demo Credentials

After running the app, register any account then use the **"Demo Seed"** button on the dashboard to instantly load the canonical demo persona:

| Field | Value |
|-------|-------|
| Target Role | AI Engineer |
| Timeline | 6 months |
| Weekly Hours | 8h |
| Python | 90% |
| Machine Learning | 70% |
| Statistics | 60% |
| Deep Learning | 40% |
| Generative AI | 20% |
| MLOps | 10% |

---

## Demo Flow (Golden Path)

1. Register → Onboarding (type "AI Engineer" as goal)
2. Dashboard → click **Demo Seed** to load canonical mastery
3. Navigate to **Skill Gap** — see Python strong, MLOps red
4. Click **Why this?** on MLOps — explanation cites 10% mastery and Docker prerequisite
5. Navigate to **Quiz** — take a quiz on "MLOps" (score poorly)
6. See mastery update banner: `MLOps 10% → X%` + "🔄 Your Learning Path Has Adapted"
7. Navigate to **My Roadmap** → click **Adapt Roadmap** → see reinforcement badges
8. Return to Dashboard — Next Best Action has updated
9. Navigate to **What-If Simulator** — reduce hours to 5/wk, run simulation
10. Navigate to **AI Mentor** — ask "Why am I learning Docker?" — contextual answer

---

## API Documentation

Interactive Swagger UI at `http://localhost:8000/docs`

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT tokens |
| POST | `/api/v1/profile` | Create learner profile (seeds mastery) |
| GET | `/api/v1/analytics/skill-gap` | Deterministic skill gap |
| GET | `/api/v1/analytics/mastery` | Current mastery map |
| GET | `/api/v1/analytics/next-best-action` | Top 3 learning priorities |
| GET | `/api/v1/analytics/explain/{skill}` | Grounded "Why this?" explanation |
| POST | `/api/v1/analytics/quiz/submit` | Score quiz + update mastery + record adaptation |
| POST | `/api/v1/analytics/whatif` | What-if simulation (stateless) |
| POST | `/api/v1/analytics/demo-seed` | Seed demo persona |
| POST | `/api/v1/roadmap` | Generate personalized roadmap |
| POST | `/api/v1/roadmap/{id}/adapt` | Adapt roadmap to current mastery |
| POST | `/api/v1/chat/message` | AI mentor chat |

---

## Tests

```bash
cd backend
python -m pytest tests/ -v
```

31 tests covering:
- Skill gap calculation (11 tests)
- Mastery update formula (7 tests)
- Quiz scoring (6 tests)
- Skill normalization (4 tests)
- Next best action (3 tests)

All pass in < 1 second (no DB or AI required).

---

## Project Structure

```
PathFinder-AI/
├── backend/
│   ├── app/
│   │   ├── ai/             AI provider abstraction (Gemini → OpenAI → OpenRouter)
│   │   ├── api/routes/     FastAPI handlers
│   │   ├── core/           Config, JWT security, dependencies
│   │   ├── db/             Async SQLAlchemy session
│   │   ├── models/         ORM models
│   │   ├── schemas/        Pydantic schemas
│   │   └── services/
│   │       ├── skill_graph.py      Deterministic skill engine (11 roles, 70+ skills)
│   │       ├── mastery_service.py  DB operations for skill mastery
│   │       └── roadmap_service.py  Roadmap persistence
│   ├── tests/              31 unit tests (pytest)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/          All page components
│   │   ├── components/     DashboardLayout (sidebar, theme toggle, switch account)
│   │   ├── store/          authStore (Zustand), themeStore (dark/light)
│   │   ├── lib/            axios API client
│   │   └── types/          Full TypeScript definitions
│   └── package.json
├── .kiro/specs/            Feature specifications
└── docker-compose.yml
```

---

## Supported Target Roles

AI Engineer · ML Engineer · Data Scientist · Full Stack Developer · Cloud Engineer ·
Software Engineer · Generative AI Engineer · Data Analyst · Backend Developer ·
DevOps Engineer · Crack GATE CSE

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, TypeScript, TailwindCSS, Zustand, Recharts, Framer Motion |
| Backend | FastAPI, Python 3.11+, SQLAlchemy 2.0, Pydantic v2 |
| Database | SQLite (dev), PostgreSQL (prod via asyncpg) |
| AI | Google Gemini 2.5 Flash (primary), OpenAI GPT-4o-mini (fallback), OpenRouter (fallback) |
| Auth | JWT (access + refresh), bcrypt |
| Tests | pytest, 31 unit tests |

---

## Built For

HCL Hackthon Round 2 Submission
Team: NeuraLearn
Repository: https://github.com/gracyjula/PathFinder-AI
