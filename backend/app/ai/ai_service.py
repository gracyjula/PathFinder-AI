"""
AI Service - Gemini + OpenAI integration for NeuraLearn.
Handles: chat, roadmap generation, skill gap analysis, quiz generation,
         career readiness scoring, weekly plan generation, mentor responses.
"""
import json
import re
from typing import Optional

import google.generativeai as genai
from openai import AsyncOpenAI

from app.core.config import settings

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Configure OpenAI client (also used for OpenRouter)
openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
openrouter_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
) if settings.OPENROUTER_API_KEY else None


def _extract_json(text: str) -> dict | list:
    """Extract JSON from markdown code blocks or raw text."""
    # Try markdown code block first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        return json.loads(match.group(1).strip())
    # Try raw JSON
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if match:
        return json.loads(match.group(1))
    raise ValueError("No JSON found in response")


async def _call_gemini(prompt: str, system: str = "", temperature: float = 0.7) -> str:
    """Call Gemini Pro with a prompt and return text response."""
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system or "You are NeuraLearn AI, an intelligent learning mentor.",
    )
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(temperature=temperature, max_output_tokens=8192),
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
    if settings.GEMINI_API_KEY and not use_openai:
        try:
            return await _call_gemini(prompt, system, temperature=temperature)
        except Exception:
            pass

    messages = [{"role": "system", "content": system or "You are NeuraLearn AI."}, {"role": "user", "content": prompt}]

    if settings.OPENAI_API_KEY:
        try:
            return await _call_openai(messages, temperature=temperature)
        except Exception:
            pass

    if settings.OPENROUTER_API_KEY:
        return await _call_openrouter(messages, temperature=temperature)

    raise RuntimeError("No AI provider configured. Set GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY.")


# ─── Core AI Functions ────────────────────────────────────────────────────────

SYSTEM_MENTOR = """You are NeuraLearn AI — an expert AI mentor, career coach, and learning path advisor.
You help learners identify their goals, analyze skill gaps, and create personalized roadmaps.
Be motivating, precise, and data-driven. Always provide structured, actionable advice."""


async def analyze_learner_intent(user_message: str, history: list[dict]) -> dict:
    """
    Analyze user message to extract: goal, current skills, experience level,
    timeline, and determine if we have enough info to generate a roadmap.
    Returns JSON with extracted data.
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
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.3)
    try:
        return _extract_json(raw)
    except Exception:
        return {"has_enough_for_roadmap": False, "follow_up_question": "Could you tell me more about your background and goals?", "intent": "onboarding"}


async def generate_roadmap(profile_data: dict) -> dict:
    """
    Generate a complete personalized learning roadmap given learner profile.
    Returns structured JSON with milestones.
    """
    prompt = f"""Create a detailed, personalized learning roadmap for this learner.

LEARNER PROFILE:
- Goal: {profile_data.get('career_goal', 'Not specified')}
- Current Skills: {', '.join(profile_data.get('current_skills', []))}
- Experience Level: {profile_data.get('experience_level', 'beginner')}
- Timeline: {profile_data.get('target_timeline_months', 12)} months
- Weekly Hours Available: {profile_data.get('weekly_hours', 10)}
- Learning Style: {profile_data.get('learning_style', 'mixed')}
- Education: {profile_data.get('education', 'Not specified')}

Generate a comprehensive roadmap with monthly milestones. Return ONLY valid JSON:
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
          "url": "https://...",
          "type": "course|video|article|project|book",
          "provider": "Provider name",
          "is_free": true,
          "duration_hours": 20,
          "why_recommended": "Reason for recommendation"
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
  "career_outcomes": ["Outcome 1", "Outcome 2"]
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.5)
    return _extract_json(raw)


async def analyze_skill_gap(current_skills: list[str], target_role: str) -> dict:
    """Analyze skill gap between current skills and target role requirements."""
    prompt = f"""Perform a comprehensive skill gap analysis.

TARGET ROLE: {target_role}
CURRENT SKILLS: {', '.join(current_skills) if current_skills else 'None'}

Return ONLY valid JSON:
{{
  "target_role": "{target_role}",
  "required_skills": ["skill1", "skill2"],
  "current_skills": {json.dumps(current_skills)},
  "missing_skills": ["missing1", "missing2"],
  "gap_percentage": 65.5,
  "skill_scores": {{"Python": 80, "ML": 60, "Deep Learning": 0}},
  "priority_skills": ["Most important skills to learn first"],
  "recommendations": ["Specific recommendation 1", "Recommendation 2"],
  "estimated_months_to_close_gap": 8
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.2)
    return _extract_json(raw)


async def generate_mentor_response(
    user_message: str,
    history: list[dict],
    profile: Optional[dict] = None,
    roadmap_context: Optional[dict] = None,
) -> str:
    """Generate a contextual mentor response."""
    context_parts = []
    if profile:
        context_parts.append(f"Learner Profile: Goal={profile.get('career_goal')}, Skills={profile.get('current_skills')}, Level={profile.get('experience_level')}")
    if roadmap_context:
        context_parts.append(f"Active Roadmap: {roadmap_context.get('title')}, Progress={roadmap_context.get('completion_percentage')}%")

    system = f"""{SYSTEM_MENTOR}

{chr(10).join(context_parts)}

You are acting as this learner's personal AI mentor. Be encouraging, specific, and practical.
Keep responses concise but complete. Use bullet points when listing multiple items."""

    # Build message history
    messages = [{"role": "system", "content": system}]
    for msg in history[-8:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    if settings.GEMINI_API_KEY:
        # Build prompt for Gemini
        hist_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in messages[1:]])
        return await _call_gemini(hist_text, system)

    if settings.OPENAI_API_KEY:
        return await _call_openai(messages)

    if settings.OPENROUTER_API_KEY:
        return await _call_openrouter(messages)

    raise RuntimeError("No AI provider configured")


async def calculate_career_readiness(profile: dict, progress_data: dict) -> dict:
    """Calculate career readiness score with breakdown."""
    prompt = f"""Calculate a career readiness score for this learner.

PROFILE:
- Goal: {profile.get('career_goal')}
- Skills: {profile.get('current_skills', [])}
- Completed Courses: {profile.get('completed_courses', [])}
- Experience Level: {profile.get('experience_level')}

PROGRESS DATA:
- Milestones Completed: {progress_data.get('milestones_completed', 0)}
- Total Milestones: {progress_data.get('total_milestones', 0)}
- Quiz Average Score: {progress_data.get('quiz_avg_score', 0)}%
- Days Active: {progress_data.get('days_active', 0)}

Return ONLY valid JSON:
{{
  "score": 78.5,
  "breakdown": {{
    "skills": 80,
    "projects": 60,
    "certifications": 40,
    "assessments": 75,
    "consistency": 85
  }},
  "weak_areas": ["Area 1", "Area 2"],
  "strong_areas": ["Strong Area 1"],
  "suggestions": ["Specific action 1", "Action 2"],
  "interview_ready": false,
  "estimated_months_to_ready": 4
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.2)
    return _extract_json(raw)


async def generate_quiz(topic: str, difficulty: str = "intermediate", num_questions: int = 5) -> dict:
    """Generate a quiz for a given topic."""
    prompt = f"""Create a quiz on "{topic}" at {difficulty} level with {num_questions} questions.

Return ONLY valid JSON:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": "q1",
      "question": "Question text?",
      "type": "mcq",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Why this is correct"
    }}
  ]
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.4)
    return _extract_json(raw)


async def generate_weekly_plan(profile: dict, current_milestone: Optional[dict] = None) -> dict:
    """Generate a personalized weekly study plan."""
    prompt = f"""Create a detailed weekly learning plan for this learner.

PROFILE:
- Goal: {profile.get('career_goal')}
- Weekly Hours: {profile.get('weekly_hours', 10)}
- Learning Style: {profile.get('learning_style', 'mixed')}
- Current Skills: {profile.get('current_skills', [])}

CURRENT MILESTONE: {json.dumps(current_milestone) if current_milestone else 'Starting fresh'}

Return ONLY valid JSON:
{{
  "week_number": 1,
  "goal": "Weekly goal statement",
  "total_hours": 10,
  "focus_topics": ["Topic 1", "Topic 2"],
  "daily_plans": [
    {{
      "day": "Monday",
      "tasks": [
        {{
          "title": "Task name",
          "type": "study|practice|project|revision",
          "duration_minutes": 60,
          "resource": "Resource name",
          "description": "What to do"
        }}
      ],
      "total_minutes": 90
    }}
  ],
  "revision_slots": ["Saturday: Review week's topics"],
  "assessment": "Weekly mini-quiz on topics covered"
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.6)
    return _extract_json(raw)


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
  "projects_found": ["Project 1", "Project 2"],
  "certifications": ["Cert 1"],
  "target_role_match": {{
    "match_percentage": 65,
    "matching_skills": ["skill1"],
    "missing_skills": ["missing1"],
    "suggestions": ["suggestion 1"]
  }}
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.2)
    return _extract_json(raw)


async def generate_skill_gap_explanation(
    skill: str,
    current_mastery: float,
    target_role: str,
    prerequisites: list[str],
    strong_skills: list[str],
) -> str:
    """
    Generate a specific, grounded explanation for why a skill is prioritized.
    The explanation references actual learner data — not a generic statement.
    """
    prereq_text = ", ".join(prerequisites) if prerequisites else "none"
    strong_text = ", ".join(strong_skills) if strong_skills else "none yet"
    prompt = f"""You are NeuraLearn AI. Write a 2-3 sentence explanation for why this learner should focus on '{skill}' next.

LEARNER DATA (use these exact numbers):
- Current mastery of '{skill}': {current_mastery:.0f}%
- Target role: {target_role}
- Prerequisites for '{skill}': {prereq_text}
- Learner's strong skills: {strong_text}

Rules:
- Reference the actual mastery percentage ({current_mastery:.0f}%)
- Mention the prerequisites if relevant
- Mention what strong skills they can build on
- Do NOT say "This course is useful for your career" — be specific
- Keep it to 2-3 sentences maximum"""

    try:
        return await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.3)
    except Exception:
        # Deterministic fallback when AI is unavailable
        prereq_note = f" It builds on {prereq_text}." if prerequisites else ""
        return (
            f"Your current mastery of {skill} is {current_mastery:.0f}%, "
            f"which is below the {target_role} target.{prereq_note} "
            f"Improving this skill will directly increase your career readiness score."
        )


async def generate_adaptation_explanation(
    skill: str,
    old_mastery: float,
    new_mastery: float,
    action_taken: str,
    target_role: str,
) -> str:
    """Explain what changed in the roadmap and why, based on mastery evidence."""
    direction = "improved" if new_mastery > old_mastery else "declined"
    delta = abs(new_mastery - old_mastery)
    prompt = f"""NeuraLearn just adapted a learner's roadmap based on new evidence. Write 2 sentences explaining what happened and why.

EVIDENCE:
- Skill: {skill}
- Mastery {direction} by {delta:.0f} points: {old_mastery:.0f}% → {new_mastery:.0f}%
- Action taken: {action_taken}
- Target role: {target_role}

Be specific. Reference the numbers. Do not be generic."""

    try:
        return await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.3)
    except Exception:
        return f"Your {skill} mastery {direction} from {old_mastery:.0f}% to {new_mastery:.0f}%. {action_taken}"


async def generate_whatif_explanation(
    original_params: dict,
    new_params: dict,
    changes: list[str],
) -> str:
    """Explain the what-if simulation result in plain language."""
    prompt = f"""A learner ran a 'what-if' simulation on their learning path. Write 3 sentences summarizing what changed and the impact.

ORIGINAL: {original_params}
SIMULATED: {new_params}
KEY CHANGES: {', '.join(changes)}

Be specific about the timeline and workload impact."""
    try:
        return await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.4)
    except Exception:
        return f"With the simulated parameters, your learning path would change: {'; '.join(changes)}."


async def generate_mock_interview_questions(role: str, skills: list[str], difficulty: str = "intermediate") -> dict:
    """Generate mock interview questions for a role."""
    prompt = f"""Generate mock interview questions for a {role} position.

CANDIDATE SKILLS: {', '.join(skills)}
DIFFICULTY: {difficulty}

Return ONLY valid JSON:
{{
  "role": "{role}",
  "sections": [
    {{
      "category": "Technical",
      "questions": [
        {{
          "question": "Question text",
          "type": "conceptual|coding|behavioral|system_design",
          "expected_topics": ["topic1"],
          "difficulty": "easy|medium|hard",
          "sample_answer": "Key points to cover"
        }}
      ]
    }},
    {{
      "category": "Behavioral",
      "questions": []
    }},
    {{
      "category": "System Design",
      "questions": []
    }}
  ],
  "tips": ["Interview tip 1", "Tip 2"]
}}"""

    raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.5)
    return _extract_json(raw)
