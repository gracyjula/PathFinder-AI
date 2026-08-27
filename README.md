# 🧠 NeuraLearn AI

> **AI-Powered Personalized Learning Operating System**
> Netflix + Duolingo + Coursera + ChatGPT + Career Coach — in one intelligent platform

---

## 🎯 What is NeuraLearn AI?

NeuraLearn AI answers the most important question every learner has:

> **"I want to become X. What should I learn next?"**

You tell the AI your goal. It analyzes your skills, identifies gaps, generates a personalized month-by-month roadmap, curates resources, and acts as your AI mentor — all in real time.

---

## ✨ Key Features

| Module | Description |
|--------|-------------|
| 🤖 **AI Mentor** | Conversational AI chat using Gemini 1.5 Pro + OpenAI fallback |
| 🎯 **Skill Gap Analyzer** | Compare current skills vs. target role requirements |
| 🗺️ **Roadmap Generator** | Month-by-month personalized learning path |
| 📊 **Career Readiness Score** | 0-100 score with breakdown and suggestions |
| 📚 **Resource Recommender** | Curated courses, videos, projects, certifications |
| 🧠 **Adaptive Learning** | Roadmap updates based on progress and quiz scores |
| 🎓 **Mock Interview** | AI-generated questions with sample answers |
| 📝 **Quiz Engine** | AI-generated quizzes per topic with evaluation |
| 📅 **Weekly Planner** | Daily schedule with tasks, revision, and assessments |
| 📄 **Resume Analyzer** | Upload resume → extract skills → gap analysis |
| 🔥 **Streak Tracking** | Daily learning streaks and consistency metrics |
| 📈 **Dashboard** | Skill radar, progress charts, milestone tracker |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NeuraLearn AI                        │
├──────────────────────┬──────────────────────────────────┤
│    Frontend          │         Backend                  │
│    React + Vite      │         FastAPI                  │
│    TypeScript        │         SQLAlchemy Async         │
│    TailwindCSS       │         PostgreSQL               │
│    Zustand           │         ChromaDB                 │
│    Recharts          │         Redis                    │
│    Framer Motion     │                                  │
├──────────────────────┴──────────────────────────────────┤
│                     AI Layer                            │
│    Gemini 1.5 Pro → OpenAI GPT-4o → OpenRouter          │
│    Automatic fallback chain                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (Docker)

### Prerequisites
- Docker & Docker Compose
- At least one AI API key (Gemini, OpenAI, or OpenRouter)

### 1. Clone and configure
```bash
git clone <repo-url>
cd NeuraLearn
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys
```

### 2. Add your API keys to `backend/.env`
```env
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key      # optional fallback
OPENROUTER_API_KEY=your-openrouter-key  # optional fallback
SECRET_KEY=your-random-secret-key-32chars-minimum
```

### 3. Start everything
```bash
docker-compose up --build
```

### 4. Access the app
| Service | URL |
|---------|-----|
| Frontend | http://localhost |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/api/docs |

---

## 💻 Local Development

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
cp .env.example .env
# Edit .env

uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Opens at http://localhost:5173
```

### Database (local)
```bash
# Start PostgreSQL (or use Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=neuralearn postgres:16-alpine
```

---

## 📡 API Endpoints

### Authentication
```
POST /api/v1/auth/register     Register new user
POST /api/v1/auth/login        Login → JWT tokens
POST /api/v1/auth/refresh      Refresh access token
GET  /api/v1/auth/me           Get current user
```

### Profile
```
POST   /api/v1/profile         Create learner profile
GET    /api/v1/profile         Get profile
PATCH  /api/v1/profile         Update profile
```

### Chat & AI Mentor
```
POST /api/v1/chat/message              Send message → AI response
GET  /api/v1/chat/sessions             List chat sessions
POST /api/v1/chat/sessions             Create session
GET  /api/v1/chat/sessions/{id}        Get session with messages
```

### Roadmap
```
GET    /api/v1/roadmap                          List roadmaps
POST   /api/v1/roadmap                          Generate new roadmap
GET    /api/v1/roadmap/{id}                     Get roadmap details
PATCH  /api/v1/roadmap/{id}/milestone/{mid}/complete   Complete milestone
DELETE /api/v1/roadmap/{id}                     Delete roadmap
```

### Analytics & AI Tools
```
GET  /api/v1/analytics/dashboard          Dashboard stats
POST /api/v1/analytics/skill-gap          Skill gap analysis
GET  /api/v1/analytics/career-readiness   Career readiness score
GET  /api/v1/analytics/weekly-plan        Weekly study plan
POST /api/v1/analytics/quiz/generate      Generate quiz
POST /api/v1/analytics/quiz/submit        Submit quiz answers
POST /api/v1/analytics/resume             Analyze resume (PDF/DOCX/TXT)
POST /api/v1/analytics/mock-interview     Generate mock interview
POST /api/v1/analytics/progress           Log learning activity
GET  /api/v1/analytics/progress           Get progress logs
```

---

## 🗄️ Database Schema

```
users                   → authentication, basic info
learner_profiles        → goals, skills, preferences
roadmaps               → AI-generated learning paths
milestones             → monthly roadmap steps (topics, resources, projects)
resources              → curated learning resources
chat_sessions          → conversation history grouping
chat_messages          → individual AI/user messages
progress_logs          → learning activity tracking
quiz_results           → quiz scores and feedback
learning_streaks       → daily streak tracking
industry_trends        → skill demand data
```

---

## 🤖 AI Integration

NeuraLearn uses a **3-tier AI fallback**:

```
1. Gemini 1.5 Pro (primary)
2. OpenAI GPT-4o mini (fallback)
3. OpenRouter (final fallback)
```

### AI Capabilities
- **Intent Analysis**: Extracts goal, skills, experience from conversation
- **Roadmap Generation**: Creates structured 12-month learning plans
- **Skill Gap Analysis**: Identifies missing skills with scores
- **Career Readiness**: Calculates readiness score with breakdown
- **Quiz Generation**: Creates topic-specific MCQs with explanations
- **Weekly Plans**: Daily study schedules with time allocation
- **Resume Analysis**: Extracts skills and matches to target role
- **Mock Interviews**: Role-specific questions with sample answers

---

## 🎨 UI Design

- **Dark theme** with glassmorphism cards
- **Gradient accents** (blue → purple)
- **Responsive** sidebar layout
- **Animated** transitions with Framer Motion
- **Interactive** milestone timeline
- **Live charts** for skill radar, progress, readiness

---

## 🧪 Demo Users (for testing)

After starting the app, register a new account. To quickly explore:

1. **Register** at http://localhost/register
2. Complete the **5-step onboarding**
3. Go to **AI Mentor** and say: *"I'm a 2nd year CS student. I know Python. I want to become an AI Engineer in 12 months."*
4. Watch the AI generate your complete roadmap!

---

## 📁 Project Structure

```
NeuraLearn/
├── backend/
│   ├── app/
│   │   ├── api/routes/     ← auth, profile, chat, roadmap, analytics, admin
│   │   ├── ai/             ← AI service (Gemini + OpenAI + OpenRouter)
│   │   ├── core/           ← config, security, dependencies
│   │   ├── db/             ← database session
│   │   ├── models/         ← SQLAlchemy ORM models
│   │   ├── schemas/        ← Pydantic request/response schemas
│   │   ├── services/       ← business logic
│   │   └── main.py         ← FastAPI app entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/     ← DashboardLayout, UI components
│   │   ├── pages/          ← Landing, Login, Register, Onboarding, Dashboard, Chat, Roadmap, Analytics, Quiz, Interview, Profile
│   │   ├── store/          ← Zustand auth store
│   │   ├── lib/            ← API client
│   │   ├── types/          ← TypeScript interfaces
│   │   └── App.tsx         ← Router
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## 🏆 Hackathon Highlights

This project demonstrates:

- ✅ **Production-ready FastAPI** with async SQLAlchemy, JWT auth, proper error handling
- ✅ **Gemini AI integration** with automatic fallback chain
- ✅ **Adaptive AI**: Roadmaps evolve based on progress and quiz performance
- ✅ **Explainable AI**: Every resource recommendation includes "why recommended"
- ✅ **Full-stack TypeScript**: Type-safe API client, Zod validation
- ✅ **Complete CRUD**: Users, profiles, roadmaps, milestones, quizzes, progress
- ✅ **Resume parsing**: PDF/DOCX/TXT with skill extraction
- ✅ **Docker-ready**: One command deployment
- ✅ **Responsive UI**: Works on mobile and desktop

---

Built with ❤️ for HCL Hackathon 2026
