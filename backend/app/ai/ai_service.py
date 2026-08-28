"""
AI Service - Gemini + OpenAI integration for NeuraLearn.
Handles: chat, roadmap generation, skill gap analysis, quiz generation,
         career readiness scoring, weekly plan generation, mentor responses.

Fallback chain: Gemini (google-genai) → OpenAI → OpenRouter
All AI calls are truly async (no event-loop blocking).
"""
import asyncio
import json
import re
from typing import Optional

from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI

from app.core.config import settings

# Configure Gemini (new google-genai SDK)
_gemini_client: Optional[genai.Client] = None
if settings.GEMINI_API_KEY:
    _gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Configure OpenAI client (also used for OpenRouter)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
openrouter_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
) if settings.OPENROUTER_API_KEY else None


def _extract_json(text: str) -> dict | list:
    """Extract JSON from markdown code blocks or raw text."""
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return json.loads(match.group(1))
    raise ValueError("No JSON found in response")


async def _call_gemini(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    """Call Gemini using the new google-genai async SDK."""
    if not _gemini_client:
        raise RuntimeError("Gemini API key not configured")
    response = await _gemini_client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            system_instruction=system or "You are NeuraLearn AI, an intelligent learning mentor.",
            temperature=temperature,
            max_output_tokens=8192,
        ),
    )
    return response.text


async def _call_openai(messages: list[dict], model: str = "gpt-4o-mini", temperature: float = 0.7) -> str:
    """Call OpenAI chat completion."""
    if not openai_client:
        raise RuntimeError("OpenAI API key not configured")
    resp = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=4096,
    )
    return resp.choices[0].message.content


async def _call_openrouter(messages: list[dict], model: str = "google/gemini-flash-1.5", temperature: float = 0.7) -> str:
    """Call OpenRouter (fallback)."""
    if not openrouter_client:
        raise RuntimeError("OpenRouter API key not configured")
    resp = await openrouter_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    return resp.choices[0].message.content


async def get_ai_response(prompt: str, system: str = "", use_openai: bool = False, temperature: float = 0.7) -> str:
    """Get AI response with automatic fallback: Gemini → OpenAI → OpenRouter."""
    if _gemini_client and not use_openai:
        try:
            return await _call_gemini(prompt, system, temperature=temperature)
        except Exception as e:
            pass  # fall through to next provider

    messages = [
        {"role": "system", "content": system or "You are NeuraLearn AI."},
        {"role": "user", "content": prompt},
    ]

    if settings.OPENAI_API_KEY:
        try:
            return await _call_openai(messages, temperature=temperature)
        except Exception:
            pass

    if settings.OPENROUTER_API_KEY:
        try:
            return await _call_openrouter(messages, temperature=temperature)
        except Exception:
            pass

    raise RuntimeError("No AI provider available. Set GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY.")


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_MENTOR = """You are NeuraLearn AI — an expert AI mentor, career coach, and learning path advisor.
You help learners identify their goals, analyze skill gaps, and create personalized roadmaps.
Be motivating, precise, and data-driven. Always provide structured, actionable advice."""


# ─── Intent Analysis ──────────────────────────────────────────────────────────

async def analyze_learner_intent(user_message: str, history: list[dict]) -> dict:
    """
    Analyze user message to extract: goal, current skills, experience level,
    timeline, and determine if we have enough info to generate a roadmap.
    """
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-6:]])

    prompt = f"""Analyze this learner's message and conversation history. Extract structured data.

CONVERSATION HISTORY:
{history_text}

CURRENT MESSAGE: {user_message}

Return a JSON object with EXACTLY this structure:
{{
  "extracted_goal": "string or null",
  "current_skills": ["skill1", "skill2"],
  "experience_level": "beginner|intermediate|advanced",
  "timeline_months": number or null,
  "education": "string or null",
  "interests": ["interest1"],
  "has_enough_for_roadmap": true/false,
  "follow_up_question": "string if more info needed, else null",
  "intent": "onboarding|question|roadmap_request|mentor_chat"
}}

IMPORTANT: Set has_enough_for_roadmap=true if the message mentions a career goal (even briefly like "AI Engineer", "data scientist", etc.)"""

    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.3)
        return _extract_json(raw)
    except Exception:
        # Deterministic fallback — check if message contains goal keywords
        goal_keywords = ["engineer", "scientist", "developer", "analyst", "architect", "designer", "manager"]
        has_goal = any(kw in user_message.lower() for kw in goal_keywords)
        return {
            "extracted_goal": user_message[:100] if has_goal else None,
            "current_skills": [],
            "experience_level": "beginner",
            "timeline_months": 12,
            "education": None,
            "interests": [],
            "has_enough_for_roadmap": has_goal,
            "follow_up_question": None if has_goal else "What career goal are you working towards?",
            "intent": "roadmap_request" if has_goal else "onboarding",
        }


# ─── Roadmap Generation ───────────────────────────────────────────────────────

async def generate_roadmap(profile_data: dict) -> dict:
    """Generate a complete personalized learning roadmap."""
    prompt = f"""Create a detailed, personalized learning roadmap for this learner.

LEARNER PROFILE:
- Goal: {profile_data.get('career_goal', 'Not specified')}
- Current Skills: {', '.join(profile_data.get('current_skills', [])) or 'None listed'}
- Experience Level: {profile_data.get('experience_level', 'beginner')}
- Timeline: {profile_data.get('target_timeline_months', 12)} months
- Weekly Hours Available: {profile_data.get('weekly_hours', 10)}
- Learning Style: {profile_data.get('learning_style', 'mixed')}
- Education: {profile_data.get('education', 'Not specified')}

Generate a roadmap with monthly milestones. Return ONLY valid JSON (no markdown text outside the JSON):
{{
  "title": "Roadmap title",
  "goal": "Career goal",
  "description": "Brief overview",
  "total_months": 12,
  "milestones": [
    {{
      "month_number": 1,
      "title": "Month 1: Topic Name",
      "description": "What this month covers",
      "topics": ["Topic 1", "Topic 2"],
      "resources": [
        {{
          "title": "Resource name",
          "url": "https://example.com",
          "type": "course|video|article|project|book",
          "provider": "Provider name",
          "is_free": true,
          "duration_hours": 20,
          "why_recommended": "Specific reason referencing the learner gap"
        }}
      ],
      "projects": [
        {{
          "title": "Project name",
          "description": "What to build",
          "difficulty": "beginner|intermediate|advanced",
          "skills_practiced": ["skill1"]
        }}
      ],
      "estimated_hours": 40,
      "difficulty": "beginner|intermediate|advanced",
      "outcomes": ["You will be able to..."]
    }}
  ],
  "skill_gaps_addressed": ["gap1", "gap2"],
  "career_outcomes": ["Outcome 1"]
}}"""

    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.5)
        data = _extract_json(raw)
        # Validate it has milestones
        if not isinstance(data.get("milestones"), list) or len(data["milestones"]) == 0:
            raise ValueError("No milestones in response")
        return data
    except Exception as e:
        # Structured fallback roadmap
        goal = profile_data.get('career_goal', 'Software Engineer')
        months = profile_data.get('target_timeline_months', 12)
        return _fallback_roadmap(goal, months, profile_data.get('current_skills', []))


def _fallback_roadmap(goal: str, months: int, current_skills: list) -> dict:
    """Deterministic fallback roadmap when AI is unavailable."""
    phases = [
        ("Foundations", "beginner", ["Core concepts", "Basic tools", "Environment setup"], 30),
        ("Core Skills", "intermediate", ["Key frameworks", "Best practices", "Projects"], 40),
        ("Advanced Topics", "intermediate", ["Advanced patterns", "Real-world projects"], 45),
        ("Specialization", "advanced", ["Domain expertise", "Portfolio projects"], 50),
    ]
    milestones = []
    per_phase = max(1, months // len(phases))
    for i, (title, diff, topics, hours) in enumerate(phases[:months]):
        milestones.append({
            "month_number": i + 1,
            "title": f"Month {i+1}: {title}",
            "description": f"Focus on {title.lower()} for {goal}",
            "topics": topics,
            "resources": [{"title": f"{topics[0]} Guide", "url": "https://roadmap.sh", "type": "article", "provider": "roadmap.sh", "is_free": True, "duration_hours": 10, "why_recommended": f"Essential for {goal} foundations"}],
            "projects": [{"title": f"{title} Project", "description": f"Build a project using {topics[0]}", "difficulty": diff, "skills_practiced": topics[:2]}],
            "estimated_hours": hours,
            "difficulty": diff,
            "outcomes": [f"Understand {topics[0]}", f"Apply {topics[-1]} in practice"],
        })
    return {
        "title": f"{goal} Roadmap",
        "goal": goal,
        "description": f"A structured {months}-month path to become a {goal}",
        "total_months": months,
        "milestones": milestones,
        "skill_gaps_addressed": [],
        "career_outcomes": [f"Qualified for {goal} roles"],
    }


# ─── Mentor Chat ──────────────────────────────────────────────────────────────

async def generate_mentor_response(
    user_message: str,
    history: list[dict],
    profile: Optional[dict] = None,
    roadmap_context: Optional[dict] = None,
    mastery_context: Optional[dict] = None,
) -> str:
    """Generate a contextual mentor response, grounded in learner's actual state."""
    context_parts = []
    if profile:
        context_parts.append(
            f"LEARNER PROFILE: Goal={profile.get('career_goal')}, "
            f"Skills={profile.get('current_skills')}, Level={profile.get('experience_level')}, "
            f"Weekly hours={profile.get('weekly_hours')}"
        )
    if roadmap_context:
        context_parts.append(
            f"ACTIVE ROADMAP: {roadmap_context.get('title')}, "
            f"Progress={roadmap_context.get('completion_percentage')}% complete"
        )
    if mastery_context:
        # Include top 5 strongest and top 3 gaps so the mentor can reference them
        sorted_mastery = sorted(mastery_context.items(), key=lambda x: x[1], reverse=True)
        strong = [(k, v) for k, v in sorted_mastery if v >= 70][:5]
        gaps = [(k, v) for k, v in sorted_mastery if v < 35][:3]
        if strong:
            context_parts.append(f"STRONG SKILLS (mastery ≥70%): " + ", ".join(f"{k} {v:.0f}%" for k, v in strong))
        if gaps:
            context_parts.append(f"SKILL GAPS (mastery <35%): " + ", ".join(f"{k} {v:.0f}%" for k, v in gaps))

    system = f"""{SYSTEM_MENTOR}

{chr(10).join(context_parts)}

You are this learner's personal AI mentor. Answer their question using the LEARNER PROFILE and mastery data above.
- When asked "Why am I learning X?", reference their actual mastery score for X and its prerequisites.
- When asked "What should I do next?", use the SKILL GAPS data.
- When asked about skipping, reference their mastery score.
- Be specific — reference actual numbers, never give generic advice.
- Keep responses concise but complete. Use bullet points when listing items."""

    messages = [{"role": "system", "content": system}]
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        if _gemini_client:
            hist_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages[1:]])
            return await _call_gemini(hist_text, system)
        if settings.OPENAI_API_KEY:
            return await _call_openai(messages)
        if settings.OPENROUTER_API_KEY:
            return await _call_openrouter(messages)
    except Exception:
        pass
    return "I'm having trouble connecting right now. Please check your API key configuration and try again."


# ─── Skill Gap (AI narrative layer) ──────────────────────────────────────────

async def analyze_skill_gap(current_skills: list[str], target_role: str) -> dict:
    """AI-assisted skill gap — used as a supplement, not primary source."""
    prompt = f"""Perform a skill gap analysis.
TARGET ROLE: {target_role}
CURRENT SKILLS: {', '.join(current_skills) if current_skills else 'None'}

Return ONLY valid JSON:
{{
  "target_role": "{target_role}",
  "required_skills": ["skill1"],
  "current_skills": {json.dumps(current_skills)},
  "missing_skills": ["missing1"],
  "gap_percentage": 65.5,
  "skill_scores": {{"Python": 80}},
  "priority_skills": ["skill1"],
  "recommendations": ["recommendation 1"],
  "estimated_months_to_close_gap": 8
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.2)
        return _extract_json(raw)
    except Exception:
        return {"target_role": target_role, "current_skills": current_skills, "missing_skills": [], "gap_percentage": 0, "skill_scores": {}, "priority_skills": [], "recommendations": [], "estimated_months_to_close_gap": 0}


# ─── Career Readiness ─────────────────────────────────────────────────────────

async def calculate_career_readiness(profile: dict, progress_data: dict) -> dict:
    """Calculate career readiness score with breakdown."""
    prompt = f"""Calculate a career readiness score for this learner.

PROFILE: Goal={profile.get('career_goal')}, Skills={profile.get('current_skills', [])}, Level={profile.get('experience_level')}
PROGRESS: Milestones={progress_data.get('milestones_completed',0)}/{progress_data.get('total_milestones',0)}, Quiz avg={progress_data.get('quiz_avg_score',0)}%, Days active={progress_data.get('days_active',0)}

Return ONLY valid JSON:
{{
  "score": 78.5,
  "breakdown": {{"skills": 80, "projects": 60, "certifications": 40, "assessments": 75, "consistency": 85}},
  "weak_areas": ["Area 1"],
  "strong_areas": ["Strong Area 1"],
  "suggestions": ["Action 1"],
  "interview_ready": false,
  "estimated_months_to_ready": 4
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.2)
        return _extract_json(raw)
    except Exception:
        score = min(100, (progress_data.get('milestones_completed', 0) / max(1, progress_data.get('total_milestones', 1))) * 100)
        return {"score": round(score, 1), "breakdown": {"skills": score, "projects": 0, "certifications": 0, "assessments": progress_data.get('quiz_avg_score', 0), "consistency": 50}, "weak_areas": [], "strong_areas": [], "suggestions": ["Keep completing milestones"], "interview_ready": score >= 80, "estimated_months_to_ready": max(1, int((100 - score) / 10))}


# ─── Quiz ─────────────────────────────────────────────────────────────────────

async def generate_quiz(topic: str, difficulty: str = "intermediate", num_questions: int = 5) -> dict:
    """Generate a quiz for a given topic."""
    prompt = f"""Create a quiz on "{topic}" at {difficulty} level with {num_questions} multiple-choice questions.

Return ONLY valid JSON:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": "q1",
      "question": "Question text?",
      "type": "mcq",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "explanation": "Why this is correct"
    }}
  ]
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.4)
        return _extract_json(raw)
    except Exception:
        return {"topic": topic, "difficulty": difficulty, "questions": [{"id": "q1", "question": f"What is a key concept in {topic}?", "type": "mcq", "options": ["Concept A", "Concept B", "Concept C", "Concept D"], "correct_answer": "Concept A", "explanation": "This is a foundational concept."}]}


# ─── Weekly Plan ──────────────────────────────────────────────────────────────

async def generate_weekly_plan(profile: dict, current_milestone: Optional[dict] = None) -> dict:
    """Generate a personalized weekly study plan."""
    prompt = f"""Create a weekly learning plan.
PROFILE: Goal={profile.get('career_goal')}, Hours/week={profile.get('weekly_hours', 10)}, Style={profile.get('learning_style', 'mixed')}
CURRENT MILESTONE: {json.dumps(current_milestone) if current_milestone else 'Starting fresh'}

Return ONLY valid JSON:
{{
  "week_number": 1,
  "goal": "Weekly goal statement",
  "total_hours": 10,
  "focus_topics": ["Topic 1"],
  "daily_plans": [
    {{
      "day": "Monday",
      "tasks": [{{"title": "Task", "type": "study", "duration_minutes": 60, "resource": "Resource", "description": "What to do"}}],
      "total_minutes": 60
    }}
  ],
  "revision_slots": ["Saturday: Review"],
  "assessment": "Weekly mini-quiz"
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.6)
        return _extract_json(raw)
    except Exception:
        hours = profile.get('weekly_hours', 10)
        return {"week_number": 1, "goal": f"Progress towards {profile.get('career_goal', 'your goal')}", "total_hours": hours, "focus_topics": [current_milestone.get("title", "Core topics")] if current_milestone else ["Foundations"], "daily_plans": [{"day": d, "tasks": [{"title": "Study session", "type": "study", "duration_minutes": max(30, (hours * 60) // 5), "resource": "Course material", "description": "Review planned topics"}], "total_minutes": max(30, (hours * 60) // 5)} for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]], "revision_slots": ["Saturday: Review week's topics"], "assessment": "End-of-week quiz on covered topics"}


# ─── Resume Analysis ──────────────────────────────────────────────────────────

async def analyze_resume(resume_text: str, target_role: Optional[str] = None) -> dict:
    """Extract skills and analyze resume against target role."""
    prompt = f"""Analyze this resume and extract structured information.

RESUME TEXT:
{resume_text[:3000]}

TARGET ROLE: {target_role or 'Not specified'}

Return ONLY valid JSON:
{{
  "extracted_skills": ["skill1", "skill2"],
  "experience_level": "beginner|intermediate|advanced",
  "education": "Degree and field",
  "work_experience_years": 2,
  "projects_found": ["Project 1"],
  "certifications": ["Cert 1"],
  "target_role_match": {{"match_percentage": 65, "matching_skills": ["skill1"], "missing_skills": ["missing1"], "suggestions": ["suggestion 1"]}}
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.2)
        return _extract_json(raw)
    except Exception:
        return {"extracted_skills": [], "experience_level": "beginner", "education": "", "work_experience_years": 0, "projects_found": [], "certifications": [], "target_role_match": {"match_percentage": 0, "matching_skills": [], "missing_skills": [], "suggestions": []}}


# ─── Mock Interview ───────────────────────────────────────────────────────────

async def generate_mock_interview_questions(role: str, skills: list[str], difficulty: str = "intermediate") -> dict:
    """Generate mock interview questions for a role."""
    prompt = f"""Generate mock interview questions for a {role} position.
CANDIDATE SKILLS: {', '.join(skills) if skills else 'General'}
DIFFICULTY: {difficulty}

Return ONLY valid JSON:
{{
  "role": "{role}",
  "sections": [
    {{"category": "Technical", "questions": [{{"question": "Question text", "type": "conceptual", "expected_topics": ["topic1"], "difficulty": "medium", "sample_answer": "Key points"}}]}},
    {{"category": "Behavioral", "questions": [{{"question": "Tell me about a challenge", "type": "behavioral", "expected_topics": ["teamwork"], "difficulty": "medium", "sample_answer": "Use STAR method"}}]}}
  ],
  "tips": ["Tip 1", "Tip 2"]
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.5)
        return _extract_json(raw)
    except Exception:
        return {"role": role, "sections": [{"category": "Technical", "questions": [{"question": f"Explain a core concept in {role}", "type": "conceptual", "expected_topics": ["fundamentals"], "difficulty": "medium", "sample_answer": "Discuss key principles"}]}], "tips": ["Research the company", "Practice coding problems"]}


# ─── Explainability ───────────────────────────────────────────────────────────

async def generate_skill_gap_explanation(
    skill: str,
    current_mastery: float,
    target_role: str,
    prerequisites: list[str],
    strong_skills: list[str],
) -> str:
    """Generate a grounded, specific explanation for why a skill is prioritized."""
    prereq_text = ", ".join(prerequisites) if prerequisites else "none"
    strong_text = ", ".join(strong_skills[:3]) if strong_skills else "none yet"
    prompt = f"""Write a 2-3 sentence explanation for why this learner should focus on '{skill}' next.

LEARNER DATA:
- Current mastery of '{skill}': {current_mastery:.0f}%
- Target role: {target_role}
- Prerequisites for '{skill}': {prereq_text}
- Learner's strong skills: {strong_text}

Rules: Reference the {current_mastery:.0f}% mastery number. Mention prerequisites if any. Do NOT say "This course is useful for your career." Be specific."""

    try:
        return await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.3)
    except Exception:
        prereq_note = f" It builds on {prereq_text}." if prerequisites and prereq_text != "none" else ""
        return (f"Your current mastery of {skill} is {current_mastery:.0f}%, which needs improvement for {target_role}.{prereq_note} "
                f"Focusing here will directly increase your career readiness score.")


async def generate_adaptation_explanation(skill: str, old_mastery: float, new_mastery: float, action_taken: str, target_role: str) -> str:
    """Explain what changed in the roadmap and why."""
    direction = "improved" if new_mastery > old_mastery else "declined"
    delta = abs(new_mastery - old_mastery)
    try:
        prompt = f"""Write 2 sentences explaining this roadmap adaptation.
Skill: {skill}, mastery {direction} by {delta:.0f} points: {old_mastery:.0f}% → {new_mastery:.0f}%
Action: {action_taken}, Target role: {target_role}
Be specific. Reference the numbers."""
        return await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.3)
    except Exception:
        return f"Your {skill} mastery {direction} from {old_mastery:.0f}% to {new_mastery:.0f}%. {action_taken}"


async def generate_whatif_explanation(original_params: dict, new_params: dict, changes: list[str]) -> str:
    """Explain the what-if simulation result."""
    try:
        prompt = f"""Write 3 sentences summarizing this learning path simulation.
ORIGINAL: {original_params}
SIMULATED: {new_params}
KEY CHANGES: {', '.join(changes)}
Be specific about timeline and workload impact."""
        return await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.4)
    except Exception:
        return f"With the simulated parameters, your learning path would change: {'; '.join(changes)}."
