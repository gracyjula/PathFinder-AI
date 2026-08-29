"""
AI Service - Gemini + OpenAI integration for NeuraLearn.
Handles: chat, roadmap generation, skill gap analysis, quiz generation,
         career readiness scoring, weekly plan generation, mentor responses.

Fallback chain: Gemini (google-genai) → OpenAI → OpenRouter
All AI calls are truly async (no event-loop blocking).
"""
import asyncio
import json
import random
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

    # Provide a helpful response even without AI — extract context from system prompt
    goal_hint = ""
    if profile:
        goal_hint = f" I can see you're working towards becoming a **{profile.get('career_goal', 'your goal')}**."

    return (
        f"I'm currently running without an AI provider configured.{goal_hint}\n\n"
        "**To enable full AI mentor capabilities**, add a Gemini API key to `backend/.env`:\n"
        "```\nGEMINI_API_KEY=your-key-here\n```\n"
        "Get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey).\n\n"
        "**What still works without AI:**\n"
        "- ✅ Skill gap analysis (deterministic)\n"
        "- ✅ Quiz generation and scoring\n"
        "- ✅ Roadmap generation (fallback)\n"
        "- ✅ Mastery tracking\n"
        "- ✅ What-if simulator\n"
        "- ✅ Dashboard analytics"
    )


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


# ─── Quiz Fallback Bank ───────────────────────────────────────────────────────
# Deterministic questions used when AI is unavailable.
# Keys are canonical lowercase topic names; each list has 5–8 MCQs.

_QUIZ_BANK: dict[str, list[dict]] = {
    "python": [
        {"id": "py1", "question": "What does the `__init__` method do in a Python class?", "type": "mcq", "options": ["Destroys the object", "Initializes instance attributes when an object is created", "Defines class-level variables", "Calls the parent class"], "correct_answer": "Initializes instance attributes when an object is created", "explanation": "`__init__` is the constructor called automatically when a new instance of a class is created."},
        {"id": "py2", "question": "Which data structure in Python allows duplicate values and maintains insertion order?", "type": "mcq", "options": ["set", "dict", "list", "frozenset"], "correct_answer": "list", "explanation": "Lists are ordered and allow duplicate elements. Sets do not allow duplicates."},
        {"id": "py3", "question": "What is the output of `[x**2 for x in range(4)]`?", "type": "mcq", "options": ["[1, 4, 9, 16]", "[0, 1, 4, 9]", "[0, 1, 2, 3]", "[1, 2, 3, 4]"], "correct_answer": "[0, 1, 4, 9]", "explanation": "range(4) yields 0, 1, 2, 3, and squaring each gives 0, 1, 4, 9."},
        {"id": "py4", "question": "Which keyword is used to handle exceptions in Python?", "type": "mcq", "options": ["catch", "except", "handle", "rescue"], "correct_answer": "except", "explanation": "Python uses try/except blocks; other languages use try/catch."},
        {"id": "py5", "question": "What does `*args` do in a function signature?", "type": "mcq", "options": ["Passes keyword arguments as a dict", "Passes positional arguments as a tuple", "Makes all arguments optional", "Enforces type checking"], "correct_answer": "Passes positional arguments as a tuple", "explanation": "`*args` collects extra positional arguments into a tuple inside the function."},
        {"id": "py6", "question": "What is the GIL in CPython?", "type": "mcq", "options": ["A garbage collection algorithm", "A lock that prevents multiple threads from executing Python bytecode simultaneously", "A GPU interface library", "A global import loader"], "correct_answer": "A lock that prevents multiple threads from executing Python bytecode simultaneously", "explanation": "The Global Interpreter Lock (GIL) means only one thread runs Python bytecode at a time, limiting CPU-bound parallelism."},
        {"id": "py7", "question": "Which module provides tools for working with iterators efficiently?", "type": "mcq", "options": ["functools", "operator", "itertools", "collections"], "correct_answer": "itertools", "explanation": "`itertools` provides fast, memory-efficient tools for creating and using iterators (chain, product, combinations, etc.)."},
        {"id": "py8", "question": "What is a Python decorator?", "type": "mcq", "options": ["A way to add comments to a function", "A function that wraps another function to extend its behavior", "A class attribute modifier", "A type hint annotation"], "correct_answer": "A function that wraps another function to extend its behavior", "explanation": "Decorators use the @syntax and wrap functions/methods to add functionality without modifying the original code."},
    ],
    "machine learning": [
        {"id": "ml1", "question": "What is overfitting in machine learning?", "type": "mcq", "options": ["The model performs well on training data but poorly on unseen data", "The model has too few parameters", "The training loss is extremely high", "The model is trained for too few epochs"], "correct_answer": "The model performs well on training data but poorly on unseen data", "explanation": "Overfitting occurs when a model memorizes training data including noise, failing to generalize."},
        {"id": "ml2", "question": "Which algorithm builds an ensemble of decision trees?", "type": "mcq", "options": ["Logistic Regression", "Support Vector Machine", "Random Forest", "K-Nearest Neighbors"], "correct_answer": "Random Forest", "explanation": "Random Forest trains many decision trees on random subsets of data and averages their predictions."},
        {"id": "ml3", "question": "What does the learning rate control in gradient descent?", "type": "mcq", "options": ["The number of training epochs", "How large a step is taken in the direction of the gradient", "The batch size", "The regularization strength"], "correct_answer": "How large a step is taken in the direction of the gradient", "explanation": "A high learning rate may overshoot minima; a low one converges slowly."},
        {"id": "ml4", "question": "What is cross-validation used for?", "type": "mcq", "options": ["Speeding up training", "Estimating model performance on unseen data reliably", "Reducing model size", "Generating synthetic data"], "correct_answer": "Estimating model performance on unseen data reliably", "explanation": "Cross-validation (e.g., k-fold) gives a reliable estimate by rotating which data is used for validation."},
        {"id": "ml5", "question": "Which metric is most appropriate for imbalanced classification?", "type": "mcq", "options": ["Accuracy", "F1-Score", "Mean Squared Error", "R² Score"], "correct_answer": "F1-Score", "explanation": "F1-Score balances precision and recall, making it better than accuracy when classes are imbalanced."},
        {"id": "ml6", "question": "What is regularization in machine learning?", "type": "mcq", "options": ["A technique to normalize input features", "Adding a penalty term to the loss to reduce model complexity", "Removing outliers from training data", "Increasing the dataset size"], "correct_answer": "Adding a penalty term to the loss to reduce model complexity", "explanation": "L1 (Lasso) and L2 (Ridge) regularization penalize large weights to prevent overfitting."},
        {"id": "ml7", "question": "What is the purpose of a validation set?", "type": "mcq", "options": ["To train the final model", "To tune hyperparameters without touching the test set", "To augment training data", "To evaluate training speed"], "correct_answer": "To tune hyperparameters without touching the test set", "explanation": "The validation set is used during development to choose hyperparameters; the test set is held out for final evaluation."},
    ],
    "deep learning": [
        {"id": "dl1", "question": "What problem does batch normalization solve?", "type": "mcq", "options": ["Reduces training data requirements", "Speeds up training by normalizing layer inputs and reducing internal covariate shift", "Prevents the model from learning", "Eliminates the need for dropout"], "correct_answer": "Speeds up training by normalizing layer inputs and reducing internal covariate shift", "explanation": "Batch normalization normalizes each mini-batch's activations, allowing higher learning rates and more stable training."},
        {"id": "dl2", "question": "What does a convolutional layer do?", "type": "mcq", "options": ["Connects every input neuron to every output neuron", "Applies learned filters to detect spatial patterns", "Reduces dimensionality via pooling", "Applies dropout regularization"], "correct_answer": "Applies learned filters to detect spatial patterns", "explanation": "Conv layers slide filters over input to produce feature maps capturing local spatial patterns like edges."},
        {"id": "dl3", "question": "What is the vanishing gradient problem?", "type": "mcq", "options": ["Gradients become too large and destabilize training", "Gradients become very small in early layers, making them learn very slowly", "The optimizer overshoots the minimum", "Dropout removes too many connections"], "correct_answer": "Gradients become very small in early layers, making them learn very slowly", "explanation": "In deep networks, gradients shrink as they backpropagate; ReLU and residual connections help mitigate this."},
        {"id": "dl4", "question": "What is dropout in neural networks?", "type": "mcq", "options": ["Removing neurons with low activation", "Randomly setting a fraction of neurons to zero during training as regularization", "Reducing the learning rate", "Pruning weights below a threshold"], "correct_answer": "Randomly setting a fraction of neurons to zero during training as regularization", "explanation": "Dropout prevents co-adaptation of neurons and acts as a form of ensemble learning."},
        {"id": "dl5", "question": "Which activation function is most commonly used in hidden layers of modern deep networks?", "type": "mcq", "options": ["Sigmoid", "Tanh", "ReLU", "Softmax"], "correct_answer": "ReLU", "explanation": "ReLU (f(x) = max(0, x)) avoids vanishing gradients and is computationally efficient."},
        {"id": "dl6", "question": "What is a residual connection (skip connection)?", "type": "mcq", "options": ["A connection that skips layers during inference only", "Adding the input of a block to its output to ease gradient flow", "A shortcut that bypasses the entire network", "A connection between encoder and decoder"], "correct_answer": "Adding the input of a block to its output to ease gradient flow", "explanation": "ResNets use skip connections so gradients can flow directly, enabling very deep networks to train effectively."},
    ],
    "nlp": [
        {"id": "nlp1", "question": "What does TF-IDF measure?", "type": "mcq", "options": ["The sentiment of a document", "How important a word is to a document relative to a corpus", "The number of sentences in a document", "The reading difficulty of text"], "correct_answer": "How important a word is to a document relative to a corpus", "explanation": "TF-IDF = Term Frequency × Inverse Document Frequency; rare words that appear often in a document score high."},
        {"id": "nlp2", "question": "What is tokenization in NLP?", "type": "mcq", "options": ["Converting text to embeddings", "Splitting text into individual units (words, subwords, characters)", "Removing stop words", "Translating between languages"], "correct_answer": "Splitting text into individual units (words, subwords, characters)", "explanation": "Tokenization is the first step in NLP pipelines, breaking raw text into processable tokens."},
        {"id": "nlp3", "question": "What are word embeddings?", "type": "mcq", "options": ["One-hot vectors for each word", "Dense vector representations that capture semantic meaning", "Frequency counts of words", "Part-of-speech tags"], "correct_answer": "Dense vector representations that capture semantic meaning", "explanation": "Word2Vec, GloVe, and FastText produce dense vectors where similar words are close in vector space."},
        {"id": "nlp4", "question": "What is named entity recognition (NER)?", "type": "mcq", "options": ["Generating new entity names", "Identifying and classifying named entities like persons, organizations, and locations in text", "Predicting the next word in a sentence", "Summarizing documents"], "correct_answer": "Identifying and classifying named entities like persons, organizations, and locations in text", "explanation": "NER is a classification task that labels spans of text as specific entity types."},
        {"id": "nlp5", "question": "What is the attention mechanism in NLP?", "type": "mcq", "options": ["A method to focus training on hard examples", "A way for models to weigh the importance of different words when encoding a sequence", "A technique to reduce vocabulary size", "An algorithm for parsing syntax trees"], "correct_answer": "A way for models to weigh the importance of different words when encoding a sequence", "explanation": "Attention allows the model to dynamically focus on relevant parts of the input when producing each output token."},
        {"id": "nlp6", "question": "What is the BLEU score used for?", "type": "mcq", "options": ["Sentiment analysis", "Evaluating machine translation by comparing n-gram overlap with reference translations", "Measuring perplexity", "Benchmarking question answering"], "correct_answer": "Evaluating machine translation by comparing n-gram overlap with reference translations", "explanation": "BLEU (Bilingual Evaluation Understudy) measures precision of n-grams in a generated translation vs references."},
    ],
    "transformers": [
        {"id": "tr1", "question": "What innovation did the 'Attention Is All You Need' paper introduce?", "type": "mcq", "options": ["Convolutional architectures for NLP", "The Transformer — replacing RNNs with self-attention for sequence modeling", "Generative Adversarial Networks", "Variational autoencoders for text"], "correct_answer": "The Transformer — replacing RNNs with self-attention for sequence modeling", "explanation": "The 2017 Vaswani et al. paper introduced the Transformer, which became the backbone of modern NLP."},
        {"id": "tr2", "question": "What does 'multi-head attention' allow?", "type": "mcq", "options": ["Training on multiple GPUs simultaneously", "The model to attend to information from different representation subspaces at different positions", "Using multiple loss functions", "Running multiple epochs in parallel"], "correct_answer": "The model to attend to information from different representation subspaces at different positions", "explanation": "Multiple attention heads can each focus on different relationships, capturing richer representations."},
        {"id": "tr3", "question": "What is positional encoding in Transformers?", "type": "mcq", "options": ["Encoding the label of each word", "Adding position information to token embeddings since Transformers lack recurrence", "A lookup table for syntax", "The position of the [CLS] token"], "correct_answer": "Adding position information to token embeddings since Transformers lack recurrence", "explanation": "Unlike RNNs, Transformers process all tokens in parallel; positional encodings inject order information."},
        {"id": "tr4", "question": "What is BERT pre-trained to do?", "type": "mcq", "options": ["Generate text autoregressively", "Predict masked tokens and next sentence prediction (bidirectional)", "Translate between languages", "Rank search results"], "correct_answer": "Predict masked tokens and next sentence prediction (bidirectional)", "explanation": "BERT uses masked language modeling (MLM) and next sentence prediction (NSP) as pre-training objectives."},
        {"id": "tr5", "question": "What is the key difference between encoder-only and decoder-only Transformers?", "type": "mcq", "options": ["Encoder-only models are larger", "Encoder-only (like BERT) are best for understanding tasks; decoder-only (like GPT) for generation", "Decoder-only models cannot process text", "There is no architectural difference"], "correct_answer": "Encoder-only (like BERT) are best for understanding tasks; decoder-only (like GPT) for generation", "explanation": "Encoder-only: bidirectional context for classification/extraction. Decoder-only: autoregressive generation."},
        {"id": "tr6", "question": "What is fine-tuning in the context of pre-trained Transformers?", "type": "mcq", "options": ["Training a Transformer from scratch on task data", "Further training a pre-trained model on a specific downstream task with a small learning rate", "Removing layers from a large model", "Quantizing weights to lower precision"], "correct_answer": "Further training a pre-trained model on a specific downstream task with a small learning rate", "explanation": "Fine-tuning adapts the general representations learned during pre-training to a specific task."},
    ],
    "generative ai": [
        {"id": "gai1", "question": "What is a Large Language Model (LLM)?", "type": "mcq", "options": ["A model that generates images from text", "A deep learning model trained on massive text corpora to understand and generate language", "A recommendation system for learning", "A database of language patterns"], "correct_answer": "A deep learning model trained on massive text corpora to understand and generate language", "explanation": "LLMs like GPT-4, Claude, and Gemini are trained on billions of tokens and can perform many language tasks."},
        {"id": "gai2", "question": "What is Retrieval-Augmented Generation (RAG)?", "type": "mcq", "options": ["A training technique for LLMs", "Combining a retrieval system with a generative model to ground responses in external documents", "A method to reduce hallucinations by removing the attention mechanism", "Generating synthetic training data"], "correct_answer": "Combining a retrieval system with a generative model to ground responses in external documents", "explanation": "RAG retrieves relevant chunks from a knowledge base and passes them as context to the LLM, reducing hallucinations."},
        {"id": "gai3", "question": "What is prompt engineering?", "type": "mcq", "options": ["Compiling prompts into machine code", "Crafting input text to guide an LLM to produce desired outputs", "Training a model on prompts", "Optimizing prompt execution speed"], "correct_answer": "Crafting input text to guide an LLM to produce desired outputs", "explanation": "Prompt engineering uses techniques like few-shot examples, chain-of-thought, and role assignment to improve LLM outputs."},
        {"id": "gai4", "question": "What does 'temperature' control in LLM sampling?", "type": "mcq", "options": ["The speed of inference", "The randomness/creativity of the model's output", "The maximum output length", "The model's context window size"], "correct_answer": "The randomness/creativity of the model's output", "explanation": "Higher temperature → more random and creative; lower temperature → more deterministic and focused."},
        {"id": "gai5", "question": "What is a vector database used for in AI applications?", "type": "mcq", "options": ["Storing traditional SQL data", "Storing and efficiently searching high-dimensional embeddings by semantic similarity", "Training neural networks", "Caching API responses"], "correct_answer": "Storing and efficiently searching high-dimensional embeddings by semantic similarity", "explanation": "Vector DBs (Pinecone, Weaviate, Chroma) enable fast ANN (approximate nearest neighbor) search over embeddings for RAG and semantic search."},
        {"id": "gai6", "question": "What is hallucination in the context of LLMs?", "type": "mcq", "options": ["The model produces visually appealing text", "The model generates plausible-sounding but factually incorrect or fabricated information", "The model imagines new training data", "High-temperature sampling artifacts"], "correct_answer": "The model generates plausible-sounding but factually incorrect or fabricated information", "explanation": "Hallucination is a key LLM limitation; techniques like RAG and fine-tuning on factual data can reduce it."},
    ],
    "mlops": [
        {"id": "mlo1", "question": "What is MLOps?", "type": "mcq", "options": ["A Python library for ML experiments", "Practices that combine ML, DevOps, and data engineering to deploy and maintain ML systems reliably", "A cloud service for training models", "A model compression technique"], "correct_answer": "Practices that combine ML, DevOps, and data engineering to deploy and maintain ML systems reliably", "explanation": "MLOps covers versioning, CI/CD for ML, monitoring, and reproducibility — the engineering discipline for production ML."},
        {"id": "mlo2", "question": "What is model drift?", "type": "mcq", "options": ["A model gradually becoming larger over time", "Degradation in model performance when the real-world data distribution changes from training data", "Random fluctuations in training loss", "Overfitting to new data"], "correct_answer": "Degradation in model performance when the real-world data distribution changes from training data", "explanation": "Data drift and concept drift can cause production models to degrade; monitoring and retraining pipelines address this."},
        {"id": "mlo3", "question": "What does a feature store do?", "type": "mcq", "options": ["Stores model weights", "Provides a centralized repository to store, share, and serve ML features for training and inference", "Compresses feature vectors", "Generates synthetic features"], "correct_answer": "Provides a centralized repository to store, share, and serve ML features for training and inference", "explanation": "Feature stores (Feast, Tecton) prevent training-serving skew and enable feature reuse across teams."},
        {"id": "mlo4", "question": "What is CI/CD in MLOps?", "type": "mcq", "options": ["Continuous Improvement and Continuous Deployment of data", "Automating the building, testing, and deployment of ML pipelines", "Collecting Insights and Curating Data", "Customer Integration and Continuous Delivery"], "correct_answer": "Automating the building, testing, and deployment of ML pipelines", "explanation": "CI/CD for ML automates retraining, validation, and deployment so new model versions can be shipped reliably."},
        {"id": "mlo5", "question": "What is an experiment tracking tool used for?", "type": "mcq", "options": ["Tracking user experiments on the app", "Logging metrics, hyperparameters, and artifacts from ML training runs for comparison", "Monitoring production API calls", "Version-controlling training datasets only"], "correct_answer": "Logging metrics, hyperparameters, and artifacts from ML training runs for comparison", "explanation": "Tools like MLflow and Weights & Biases track experiments so teams can reproduce results and compare model versions."},
        {"id": "mlo6", "question": "What is canary deployment in ML serving?", "type": "mcq", "options": ["Deploying to a staging environment only", "Gradually rolling out a new model to a small fraction of traffic before full deployment", "Using lightweight (canary) models for edge devices", "Deploying models trained on minority class data"], "correct_answer": "Gradually rolling out a new model to a small fraction of traffic before full deployment", "explanation": "Canary deployment limits blast radius; if the new model performs poorly, you can quickly roll back."},
    ],
    "docker": [
        {"id": "dok1", "question": "What is a Docker image?", "type": "mcq", "options": ["A running instance of an application", "A read-only template with instructions to create a Docker container", "A virtual machine snapshot", "A Docker network configuration"], "correct_answer": "A read-only template with instructions to create a Docker container", "explanation": "Images are immutable blueprints; containers are running instances created from images."},
        {"id": "dok2", "question": "What does `docker-compose up` do?", "type": "mcq", "options": ["Builds a single Docker image", "Starts and orchestrates multiple containers defined in docker-compose.yml", "Pushes an image to Docker Hub", "Creates a Docker volume"], "correct_answer": "Starts and orchestrates multiple containers defined in docker-compose.yml", "explanation": "docker-compose manages multi-container applications; `up` builds (if needed) and starts all services."},
        {"id": "dok3", "question": "What is a Dockerfile?", "type": "mcq", "options": ["A YAML config for container orchestration", "A text file with instructions to build a Docker image layer by layer", "A Docker network definition", "A log file for Docker daemon"], "correct_answer": "A text file with instructions to build a Docker image layer by layer", "explanation": "Dockerfiles use instructions like FROM, RUN, COPY, CMD to define how to build an image."},
        {"id": "dok4", "question": "What is the purpose of Docker volumes?", "type": "mcq", "options": ["To compress container images", "To persist data outside the container lifecycle", "To share CPU resources between containers", "To expose container ports to the host"], "correct_answer": "To persist data outside the container lifecycle", "explanation": "Volumes store data on the host or a managed location so it survives container restarts and removals."},
        {"id": "dok5", "question": "What command runs a container interactively?", "type": "mcq", "options": ["`docker build -t`", "`docker run -it`", "`docker exec -d`", "`docker start --attach`"], "correct_answer": "`docker run -it`", "explanation": "`-i` keeps stdin open, `-t` allocates a pseudo-TTY, allowing interactive shell sessions."},
        {"id": "dok6", "question": "What is a multi-stage Docker build used for?", "type": "mcq", "options": ["Running multiple containers simultaneously", "Separating build-time dependencies from the final runtime image to reduce image size", "Building images for multiple architectures", "Caching layers more aggressively"], "correct_answer": "Separating build-time dependencies from the final runtime image to reduce image size", "explanation": "Multi-stage builds use multiple FROM statements; only the final stage is shipped, discarding build tools."},
    ],
    "statistics": [
        {"id": "st1", "question": "What is the Central Limit Theorem?", "type": "mcq", "options": ["The mean of a dataset equals its median for normal distributions", "The sampling distribution of the mean approaches normality as sample size increases, regardless of population distribution", "All probability distributions converge to uniform", "Large datasets always have small variance"], "correct_answer": "The sampling distribution of the mean approaches normality as sample size increases, regardless of population distribution", "explanation": "CLT is foundational for inferential statistics — it justifies using normal-distribution-based tests on large samples."},
        {"id": "st2", "question": "What does p-value represent in hypothesis testing?", "type": "mcq", "options": ["The probability that the null hypothesis is true", "The probability of observing results as extreme as the data, assuming the null hypothesis is true", "The power of the statistical test", "The effect size"], "correct_answer": "The probability of observing results as extreme as the data, assuming the null hypothesis is true", "explanation": "A small p-value (< 0.05) suggests the data is unlikely under H₀, providing evidence to reject it."},
        {"id": "st3", "question": "What is the difference between Type I and Type II errors?", "type": "mcq", "options": ["Type I: false negative; Type II: false positive", "Type I: false positive (rejecting a true null); Type II: false negative (failing to reject a false null)", "Type I is more serious than Type II always", "They are the same error measured differently"], "correct_answer": "Type I: false positive (rejecting a true null); Type II: false negative (failing to reject a false null)", "explanation": "Type I (α) = false alarm; Type II (β) = missed detection. There is a trade-off between them."},
        {"id": "st4", "question": "What is Bayesian inference?", "type": "mcq", "options": ["Frequency-based probability estimation", "Updating prior beliefs with observed evidence to obtain a posterior distribution", "A method for non-parametric testing", "Maximum likelihood estimation"], "correct_answer": "Updating prior beliefs with observed evidence to obtain a posterior distribution", "explanation": "Bayes' theorem: P(θ|data) ∝ P(data|θ) × P(θ). NeuraLearn uses Bayesian updating for mastery scores."},
        {"id": "st5", "question": "What does standard deviation measure?", "type": "mcq", "options": ["The average value in a dataset", "The spread or dispersion of data around the mean", "The most frequent value", "The difference between max and min values"], "correct_answer": "The spread or dispersion of data around the mean", "explanation": "Standard deviation is the square root of variance; larger values mean data is more spread out."},
        {"id": "st6", "question": "What is correlation vs. causation?", "type": "mcq", "options": ["They are interchangeable in statistics", "Correlation measures linear association; causation means one variable directly causes another", "Causation implies perfect correlation", "Correlation only applies to categorical data"], "correct_answer": "Correlation measures linear association; causation means one variable directly causes another", "explanation": "A classic fallacy: correlation ≠ causation. Establishing causation requires controlled experiments or causal inference methods."},
    ],
    "data structures": [
        {"id": "ds1", "question": "What is the time complexity of searching in a balanced binary search tree?", "type": "mcq", "options": ["O(1)", "O(n)", "O(log n)", "O(n log n)"], "correct_answer": "O(log n)", "explanation": "In a balanced BST (AVL, Red-Black), height is O(log n), so search, insert, and delete are all O(log n)."},
        {"id": "ds2", "question": "What data structure is LIFO (Last In, First Out)?", "type": "mcq", "options": ["Queue", "Stack", "Heap", "Linked List"], "correct_answer": "Stack", "explanation": "A stack follows LIFO — the last element pushed is the first popped. Used in call stacks, undo operations, and DFS."},
        {"id": "ds3", "question": "What is the worst-case time complexity of quicksort?", "type": "mcq", "options": ["O(n log n)", "O(n)", "O(n²)", "O(log n)"], "correct_answer": "O(n²)", "explanation": "QuickSort worst case is O(n²) when the pivot is always the min/max (already sorted data with naïve pivot). Average is O(n log n)."},
        {"id": "ds4", "question": "What is a hash table?", "type": "mcq", "options": ["A sorted array with binary search", "A data structure that maps keys to values using a hash function for O(1) average-case access", "A tree where every node stores a hash", "A queue with hash-based prioritization"], "correct_answer": "A data structure that maps keys to values using a hash function for O(1) average-case access", "explanation": "Hash tables provide average O(1) insert, delete, and lookup using a hash function to compute bucket indices."},
        {"id": "ds5", "question": "What is a graph's adjacency list representation?", "type": "mcq", "options": ["A matrix where entry (i,j) = 1 if edge exists", "Each vertex stores a list of its neighboring vertices", "A list of all edges in the graph", "A sorted list of vertices by degree"], "correct_answer": "Each vertex stores a list of its neighboring vertices", "explanation": "Adjacency lists are memory-efficient for sparse graphs; adjacency matrices are O(V²) space but O(1) edge lookup."},
        {"id": "ds6", "question": "What is the primary advantage of a heap data structure?", "type": "mcq", "options": ["O(1) search", "O(log n) insertion and O(1) min/max access", "O(n) deletion", "Sorted iteration in O(n)"], "correct_answer": "O(log n) insertion and O(1) min/max access", "explanation": "Min/max heaps give O(1) access to the minimum/maximum element and O(log n) for insert/delete — ideal for priority queues."},
    ],
    "system design": [
        {"id": "sd1", "question": "What is horizontal scaling?", "type": "mcq", "options": ["Upgrading a single server with more RAM/CPU", "Adding more machines to distribute load", "Increasing the storage capacity of a database", "Vertical partitioning of a database"], "correct_answer": "Adding more machines to distribute load", "explanation": "Horizontal scaling (scale-out) adds more nodes; vertical scaling (scale-up) upgrades existing nodes. Horizontal is more resilient."},
        {"id": "sd2", "question": "What is a CDN (Content Delivery Network)?", "type": "mcq", "options": ["A type of database", "Geographically distributed servers that cache and deliver content from locations closer to users", "A container networking driver", "A DNS load balancer"], "correct_answer": "Geographically distributed servers that cache and deliver content from locations closer to users", "explanation": "CDNs reduce latency by serving static assets (images, JS) from edge nodes near the user."},
        {"id": "sd3", "question": "What is the CAP theorem?", "type": "mcq", "options": ["A distributed system can optimize CPU, API, and Partitioning simultaneously", "A distributed system can guarantee only two of Consistency, Availability, and Partition tolerance", "All distributed databases must choose between SQL and NoSQL", "Cache, API, and Proxy design principles"], "correct_answer": "A distributed system can guarantee only two of Consistency, Availability, and Partition tolerance", "explanation": "CAP theorem (Brewer, 2000): in a network partition, you must choose between consistency and availability."},
        {"id": "sd4", "question": "What is a message queue used for in system design?", "type": "mcq", "options": ["Storing user sessions", "Decoupling producers from consumers to enable async processing and absorb traffic spikes", "Caching database query results", "Load balancing HTTP requests"], "correct_answer": "Decoupling producers from consumers to enable async processing and absorb traffic spikes", "explanation": "Message queues (Kafka, RabbitMQ, SQS) allow systems to handle varying load and provide fault isolation between services."},
        {"id": "sd5", "question": "What is database sharding?", "type": "mcq", "options": ["Creating read replicas for a database", "Partitioning data across multiple database instances to distribute load", "Encrypting database at rest", "Removing unused indexes"], "correct_answer": "Partitioning data across multiple database instances to distribute load", "explanation": "Sharding splits data (e.g., by user_id range or hash) across machines so no single instance holds all data."},
    ],
    "langchain": [
        {"id": "lc1", "question": "What is LangChain's primary purpose?", "type": "mcq", "options": ["A database for storing language model outputs", "A framework for building applications with LLMs by chaining components like prompts, models, and tools", "A fine-tuning library for transformers", "A deployment platform for ML models"], "correct_answer": "A framework for building applications with LLMs by chaining components like prompts, models, and tools", "explanation": "LangChain simplifies building LLM apps by providing abstractions for chains, agents, memory, and tool use."},
        {"id": "lc2", "question": "What is a LangChain 'chain'?", "type": "mcq", "options": ["A blockchain for AI transactions", "A sequence of calls to LLMs, tools, or data sources composed together", "A tokenization pipeline", "A type of attention mechanism"], "correct_answer": "A sequence of calls to LLMs, tools, or data sources composed together", "explanation": "Chains combine prompts, LLM calls, and post-processing steps into reusable, composable pipelines."},
        {"id": "lc3", "question": "What is a LangChain agent?", "type": "mcq", "options": ["A human user of the system", "An LLM that uses reasoning to decide which tools to call and in what order to complete a task", "A static chain with no branching", "A monitoring component"], "correct_answer": "An LLM that uses reasoning to decide which tools to call and in what order to complete a task", "explanation": "Agents (ReAct, tool-calling) dynamically choose and invoke tools based on the task, enabling open-ended reasoning."},
        {"id": "lc4", "question": "What is 'memory' in LangChain?", "type": "mcq", "options": ["GPU memory allocation", "A component that persists conversation history or facts across interactions", "Model weight storage", "A caching layer for embeddings"], "correct_answer": "A component that persists conversation history or facts across interactions", "explanation": "Memory types (ConversationBufferMemory, VectorStoreMemory) allow chains/agents to reference previous turns."},
        {"id": "lc5", "question": "What is LangChain Expression Language (LCEL)?", "type": "mcq", "options": ["A new programming language for AI", "A declarative way to compose chains using the | pipe operator for streaming and parallelism", "A DSL for writing prompts", "A schema definition language for LLM outputs"], "correct_answer": "A declarative way to compose chains using the | pipe operator for streaming and parallelism", "explanation": "LCEL (e.g., prompt | model | parser) enables first-class streaming, async, and batch execution."},
    ],
    "sql": [
        {"id": "sql1", "question": "What is the difference between INNER JOIN and LEFT JOIN?", "type": "mcq", "options": ["They are identical", "INNER JOIN returns only matched rows; LEFT JOIN returns all rows from the left table plus matched rows from the right", "LEFT JOIN is faster than INNER JOIN", "INNER JOIN includes NULL rows from both tables"], "correct_answer": "INNER JOIN returns only matched rows; LEFT JOIN returns all rows from the left table plus matched rows from the right", "explanation": "LEFT JOIN preserves all left-table rows, filling NULL for unmatched right-table columns."},
        {"id": "sql2", "question": "What does the GROUP BY clause do?", "type": "mcq", "options": ["Sorts the result set", "Groups rows with the same values into summary rows for aggregate functions", "Filters rows before aggregation", "Removes duplicate rows"], "correct_answer": "Groups rows with the same values into summary rows for aggregate functions", "explanation": "GROUP BY is used with COUNT, SUM, AVG, etc. to produce one row per group."},
        {"id": "sql3", "question": "What is a database index?", "type": "mcq", "options": ["A backup copy of a table", "A data structure that improves the speed of data retrieval at the cost of additional storage and write overhead", "The primary key of a table", "A materialized view"], "correct_answer": "A data structure that improves the speed of data retrieval at the cost of additional storage and write overhead", "explanation": "B-tree and hash indexes allow the database to find rows without full-table scans, dramatically speeding up queries."},
        {"id": "sql4", "question": "What is the difference between WHERE and HAVING?", "type": "mcq", "options": ["They are interchangeable", "WHERE filters rows before grouping; HAVING filters groups after GROUP BY", "HAVING works on individual rows; WHERE works on groups", "WHERE is for SELECT; HAVING is for UPDATE"], "correct_answer": "WHERE filters rows before grouping; HAVING filters groups after GROUP BY", "explanation": "Use HAVING to filter on aggregate results (e.g., HAVING COUNT(*) > 5) and WHERE to filter raw rows."},
        {"id": "sql5", "question": "What is a transaction in a database?", "type": "mcq", "options": ["A single SELECT query", "A sequence of operations treated as a single atomic unit (all succeed or all fail)", "A database backup operation", "A stored procedure call"], "correct_answer": "A sequence of operations treated as a single atomic unit (all succeed or all fail)", "explanation": "Transactions ensure ACID properties (Atomicity, Consistency, Isolation, Durability) — critical for data integrity."},
    ],
    "cloud": [
        {"id": "cld1", "question": "What is Infrastructure as a Service (IaaS)?", "type": "mcq", "options": ["Pre-built application software delivered over the internet", "Virtualized computing resources (VMs, storage, networking) provided on-demand over the internet", "Managed platform for deploying code without managing servers", "AI models served via API"], "correct_answer": "Virtualized computing resources (VMs, storage, networking) provided on-demand over the internet", "explanation": "IaaS (EC2, Azure VMs, GCE) gives you raw compute; you manage OS and above. PaaS manages the runtime too."},
        {"id": "cld2", "question": "What is serverless computing?", "type": "mcq", "options": ["Running servers without cooling systems", "A model where you run functions without managing underlying servers; pay per invocation", "Using containers instead of VMs", "Auto-scaling with no manual configuration"], "correct_answer": "A model where you run functions without managing underlying servers; pay per invocation", "explanation": "AWS Lambda, Google Cloud Functions, and Azure Functions are serverless; the provider manages infrastructure."},
        {"id": "cld3", "question": "What is an SLA (Service Level Agreement) in cloud services?", "type": "mcq", "options": ["A security policy document", "A contract defining the expected uptime, performance, and support guarantees from the provider", "A list of available cloud regions", "A billing agreement"], "correct_answer": "A contract defining the expected uptime, performance, and support guarantees from the provider", "explanation": "SLAs specify availability targets (e.g., 99.99% uptime) and the remedies if they are not met."},
        {"id": "cld4", "question": "What is auto-scaling in cloud computing?", "type": "mcq", "options": ["Automatically updating software dependencies", "Dynamically adjusting the number of compute resources based on demand", "Scaling database storage automatically", "Automatically backing up data"], "correct_answer": "Dynamically adjusting the number of compute resources based on demand", "explanation": "Auto-scaling groups add/remove instances based on metrics (CPU, requests/sec), ensuring cost efficiency and availability."},
        {"id": "cld5", "question": "What is the Shared Responsibility Model in cloud security?", "type": "mcq", "options": ["Security is entirely the cloud provider's responsibility", "Security is divided: provider secures the infrastructure; customer secures their data, applications, and configurations", "The customer has no security responsibilities", "Security responsibilities are negotiated per contract"], "correct_answer": "Security is divided: provider secures the infrastructure; customer secures their data, applications, and configurations", "explanation": "AWS/GCP/Azure are responsible for the cloud; you are responsible for security in the cloud (data, IAM, app config)."},
    ],
    "data science": [
        {"id": "dsc1", "question": "What is exploratory data analysis (EDA)?", "type": "mcq", "options": ["Training a machine learning model on all data", "Analyzing datasets to summarize their characteristics, find patterns, and identify anomalies before modeling", "Splitting data into train/test sets", "Deploying a model to production"], "correct_answer": "Analyzing datasets to summarize their characteristics, find patterns, and identify anomalies before modeling", "explanation": "EDA uses statistics and visualization (histograms, scatter plots, correlation matrices) to understand the data."},
        {"id": "dsc2", "question": "What is feature engineering?", "type": "mcq", "options": ["Selecting the best ML algorithm", "Creating, transforming, or selecting variables from raw data to improve model performance", "Evaluating model metrics", "Scaling the dataset size"], "correct_answer": "Creating, transforming, or selecting variables from raw data to improve model performance", "explanation": "Good features (log transforms, interaction terms, aggregations) can improve a simple model more than a complex model on raw data."},
        {"id": "dsc3", "question": "What does the Pandas `groupby` operation do?", "type": "mcq", "options": ["Merges two DataFrames", "Splits data into groups and applies aggregate functions to each group", "Sorts a DataFrame by column", "Removes duplicate rows"], "correct_answer": "Splits data into groups and applies aggregate functions to each group", "explanation": "`df.groupby('col').agg(func)` is the split-apply-combine pattern for aggregation in Pandas."},
        {"id": "dsc4", "question": "What is data normalization?", "type": "mcq", "options": ["Removing outliers from data", "Scaling features to a common range (e.g., 0–1) to prevent features with large values from dominating", "Encoding categorical variables", "Imputing missing values"], "correct_answer": "Scaling features to a common range (e.g., 0–1) to prevent features with large values from dominating", "explanation": "Min-Max scaling and standardization (z-score) are common normalization techniques used before distance-based algorithms."},
        {"id": "dsc5", "question": "What is a confusion matrix?", "type": "mcq", "options": ["A heatmap of feature correlations", "A table showing True Positives, False Positives, True Negatives, and False Negatives for a classifier", "A matrix of model hyperparameters", "A performance comparison table for multiple models"], "correct_answer": "A table showing True Positives, False Positives, True Negatives, and False Negatives for a classifier", "explanation": "Confusion matrices summarize classification performance, from which precision, recall, F1, and accuracy can be derived."},
    ],
    "javascript": [
        {"id": "js1", "question": "What is the difference between `let`, `const`, and `var`?", "type": "mcq", "options": ["They are all identical", "`var` is function-scoped and hoisted; `let` and `const` are block-scoped; `const` cannot be reassigned", "`let` is global; `var` is local", "`const` prevents object mutations"], "correct_answer": "`var` is function-scoped and hoisted; `let` and `const` are block-scoped; `const` cannot be reassigned", "explanation": "Prefer `const` by default, `let` when reassignment is needed. Avoid `var` to prevent scoping bugs."},
        {"id": "js2", "question": "What is a Promise in JavaScript?", "type": "mcq", "options": ["A guarantee of no bugs", "An object representing the eventual completion or failure of an async operation", "A function that runs synchronously", "A way to declare variables"], "correct_answer": "An object representing the eventual completion or failure of an async operation", "explanation": "Promises have three states: pending, fulfilled, rejected. They replaced callbacks and are used with async/await."},
        {"id": "js3", "question": "What does the spread operator `...` do?", "type": "mcq", "options": ["Creates a new function", "Spreads iterable elements into individual elements (expanding arrays/objects)", "Declares a rest parameter", "Loops over an array"], "correct_answer": "Spreads iterable elements into individual elements (expanding arrays/objects)", "explanation": "`[...arr1, ...arr2]` merges arrays; `{...obj1, ...obj2}` merges objects. Also used in function calls."},
        {"id": "js4", "question": "What is event bubbling in the DOM?", "type": "mcq", "options": ["A way to create custom events", "Events propagate from the target element up through the DOM tree to the document root", "Events that occur repeatedly", "Browser animations triggered by JS events"], "correct_answer": "Events propagate from the target element up through the DOM tree to the document root", "explanation": "Bubbling allows parent handlers to catch child element events. `event.stopPropagation()` prevents it."},
        {"id": "js5", "question": "What is the event loop in JavaScript?", "type": "mcq", "options": ["A for loop over DOM events", "The mechanism that allows JS to be non-blocking by executing callbacks from the queue when the call stack is empty", "A setInterval wrapper", "A process for handling memory allocation"], "correct_answer": "The mechanism that allows JS to be non-blocking by executing callbacks from the queue when the call stack is empty", "explanation": "JS is single-threaded; the event loop + callback queue allow async operations (I/O, timers) to not block execution."},
    ],
    "react": [
        {"id": "rct1", "question": "What is the virtual DOM in React?", "type": "mcq", "options": ["A browser API for 3D rendering", "An in-memory representation of the real DOM; React diffs it to minimize actual DOM updates", "A hidden DOM for testing", "The DOM used by server-side rendering"], "correct_answer": "An in-memory representation of the real DOM; React diffs it to minimize actual DOM updates", "explanation": "React's reconciler compares virtual DOM snapshots and batches minimal real DOM updates for performance."},
        {"id": "rct2", "question": "What is the purpose of `useEffect` hook?", "type": "mcq", "options": ["To manage component state", "To perform side effects (data fetching, subscriptions, DOM mutations) after render", "To memoize a function", "To access context values"], "correct_answer": "To perform side effects (data fetching, subscriptions, DOM mutations) after render", "explanation": "`useEffect(() => { ... }, [deps])` runs after render; the dependency array controls when it re-runs."},
        {"id": "rct3", "question": "What is prop drilling and how is it solved?", "type": "mcq", "options": ["A performance issue with deep component trees; solved by using useMemo", "Passing props through many intermediate components; solved by Context API or state management (Zustand, Redux)", "A bug caused by mutating props; solved by immutable updates", "Rendering components too deeply; solved by code splitting"], "correct_answer": "Passing props through many intermediate components; solved by Context API or state management (Zustand, Redux)", "explanation": "Prop drilling makes code brittle; Context provides global values without explicit passing at every level."},
        {"id": "rct4", "question": "What does the `key` prop do in lists?", "type": "mcq", "options": ["Assigns CSS styles to list items", "Helps React identify which items have changed for efficient reconciliation", "Defines the render order of elements", "Prevents re-renders of list items"], "correct_answer": "Helps React identify which items have changed for efficient reconciliation", "explanation": "Without keys, React may unnecessarily re-render or reorder list items incorrectly. Use stable, unique IDs as keys."},
        {"id": "rct5", "question": "What is React Query (TanStack Query) used for?", "type": "mcq", "options": ["Querying the virtual DOM", "Server state management: fetching, caching, synchronizing, and updating data from APIs", "Writing SQL queries in React", "Testing React components"], "correct_answer": "Server state management: fetching, caching, synchronizing, and updating data from APIs", "explanation": "React Query handles loading states, caching, background refetching, and invalidation — removing the need for manual fetch logic."},
        {"id": "rct6", "question": "What is the difference between `useMemo` and `useCallback`?", "type": "mcq", "options": ["They are the same", "`useMemo` memoizes a computed value; `useCallback` memoizes a function reference", "`useMemo` is for async; `useCallback` for sync", "`useCallback` caches API responses"], "correct_answer": "`useMemo` memoizes a computed value; `useCallback` memoizes a function reference", "explanation": "Both prevent unnecessary recalculation/recreation. `useMemo(() => compute(), [deps])` and `useCallback(() => fn(), [deps])`."},
    ],
    "node.js": [
        {"id": "nd1", "question": "What makes Node.js non-blocking?", "type": "mcq", "options": ["It uses multiple threads for I/O", "It uses an event-driven, single-threaded event loop with async I/O via libuv", "It compiles JavaScript to native code", "It uses worker processes for all operations"], "correct_answer": "It uses an event-driven, single-threaded event loop with async I/O via libuv", "explanation": "Node.js offloads I/O to libuv's thread pool and gets callbacks via the event loop, enabling high concurrency."},
        {"id": "nd2", "question": "What is the purpose of `package.json`?", "type": "mcq", "options": ["To store environment variables", "To define project metadata, dependencies, scripts, and module entry points", "To configure TypeScript compilation", "To declare API routes"], "correct_answer": "To define project metadata, dependencies, scripts, and module entry points", "explanation": "`package.json` is the manifest for Node projects; npm/yarn/pnpm use it to install dependencies and run scripts."},
        {"id": "nd3", "question": "What is middleware in Express.js?", "type": "mcq", "options": ["A database connection pool", "Functions that have access to req, res, and next — used for auth, logging, error handling in the request pipeline", "A caching layer between the app and database", "A testing utility"], "correct_answer": "Functions that have access to req, res, and next — used for auth, logging, error handling in the request pipeline", "explanation": "Middleware can modify req/res, end the cycle, or call `next()` to pass control to the next function."},
        {"id": "nd4", "question": "What is the difference between `require()` and ES `import`?", "type": "mcq", "options": ["They are identical", "`require()` is CommonJS (dynamic, synchronous); `import` is ES Modules (static, tree-shakeable)", "`import` only works in browsers", "`require()` is async by default"], "correct_answer": "`require()` is CommonJS (dynamic, synchronous); `import` is ES Modules (static, tree-shakeable)", "explanation": "Node.js supports both; ES Modules (`.mjs` or `type: module`) are the modern standard and enable tree-shaking."},
        {"id": "nd5", "question": "What is `async/await` in Node.js?", "type": "mcq", "options": ["A library for async operations", "Syntactic sugar over Promises that lets you write async code in a synchronous style", "A new thread model", "A way to run blocking code asynchronously"], "correct_answer": "Syntactic sugar over Promises that lets you write async code in a synchronous style", "explanation": "`await` pauses execution within an `async` function until the Promise resolves, without blocking the event loop."},
    ],
}

# Alias map for fuzzy topic matching
_TOPIC_ALIASES: dict[str, str] = {
    "ml": "machine learning",
    "dl": "deep learning",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "generative artificial intelligence": "generative ai",
    "llm": "generative ai",
    "llms": "generative ai",
    "large language models": "generative ai",
    "natural language processing": "nlp",
    "transformer": "transformers",
    "bert": "transformers",
    "gpt": "transformers",
    "mlops": "mlops",
    "ml operations": "mlops",
    "containers": "docker",
    "containerization": "docker",
    "stats": "statistics",
    "probability": "statistics",
    "dsa": "data structures",
    "algorithms": "data structures",
    "data structures and algorithms": "data structures",
    "system design interview": "system design",
    "distributed systems": "system design",
    "langchain": "langchain",
    "lang chain": "langchain",
    "mysql": "sql",
    "postgresql": "sql",
    "databases": "sql",
    "relational databases": "sql",
    "aws": "cloud",
    "gcp": "cloud",
    "azure": "cloud",
    "cloud computing": "cloud",
    "ds": "data science",
    "data analysis": "data science",
    "js": "javascript",
    "es6": "javascript",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "express": "node.js",
    "expressjs": "node.js",
}


def _get_fallback_questions(topic: str, num_questions: int) -> list[dict]:
    """Return num_questions questions from the fallback bank for the given topic."""
    key = topic.lower().strip()
    key = _TOPIC_ALIASES.get(key, key)
    questions = _QUIZ_BANK.get(key)

    # Fuzzy fallback: find partial match
    if not questions:
        for bank_key, bank_questions in _QUIZ_BANK.items():
            if key in bank_key or bank_key in key:
                questions = bank_questions
                break

    # Last resort: python basics
    if not questions:
        questions = _QUIZ_BANK["python"]

    selected = random.sample(questions, min(num_questions, len(questions)))
    # Renumber IDs for the selection
    for i, q in enumerate(selected, 1):
        q = dict(q)  # copy so we don't mutate the bank
        selected[i - 1] = {**q, "id": f"q{i}"}
    return selected


# ─── Mock Interview Fallback Bank ─────────────────────────────────────────────

_INTERVIEW_BANK: dict[str, dict[str, list[dict]]] = {
    "AI Engineer": {
        "technical": [
            {"question": "Explain the difference between supervised, unsupervised, and reinforcement learning with examples.", "type": "conceptual", "expected_topics": ["supervised", "unsupervised", "RL", "labeling"], "difficulty": "medium", "sample_answer": "Supervised: labeled data (classification, regression). Unsupervised: no labels, find structure (clustering, anomaly detection). RL: agent learns via rewards in an environment (game playing, robotics)."},
            {"question": "How does the attention mechanism in Transformers work, and why did it replace RNNs for NLP?", "type": "technical", "expected_topics": ["attention", "self-attention", "transformer", "parallelism"], "difficulty": "hard", "sample_answer": "Attention computes weighted sums over all positions, allowing the model to focus on relevant tokens. Unlike RNNs, Transformers process all tokens in parallel, avoiding vanishing gradients and enabling much longer context."},
            {"question": "You have a model that performs well on validation but poorly in production. Walk me through your debugging process.", "type": "problem-solving", "expected_topics": ["distribution shift", "data drift", "logging", "monitoring", "A/B test"], "difficulty": "hard", "sample_answer": "Check training-serving skew first. Analyze production input distribution vs training data. Add logging to capture input features at inference time. Use shadow mode testing. Check for stale features in the feature pipeline."},
            {"question": "What is Retrieval-Augmented Generation (RAG) and when would you use it over fine-tuning?", "type": "conceptual", "expected_topics": ["RAG", "fine-tuning", "knowledge base", "hallucination", "up-to-date"], "difficulty": "medium", "sample_answer": "RAG retrieves relevant docs and passes them as context. Use RAG when: knowledge changes frequently, you need citations, or the knowledge base is too large to fine-tune on. Use fine-tuning for style, format, or domain-specific reasoning patterns."},
            {"question": "Describe how you would evaluate an LLM-based application in production.", "type": "technical", "expected_topics": ["evals", "RAGAS", "human feedback", "hallucination rate", "latency", "cost"], "difficulty": "hard", "sample_answer": "Combine automated metrics (BLEU, ROUGE, RAGAS for RAG) with LLM-as-judge scoring and periodic human review. Track latency, cost per call, hallucination rate, and user satisfaction signals. Use A/B testing for model versions."},
        ],
        "behavioral": [
            {"question": "Tell me about a time you had to explain a complex ML concept to a non-technical stakeholder.", "type": "behavioral", "expected_topics": ["communication", "simplification", "impact"], "difficulty": "medium", "sample_answer": "Use STAR: Situation (explain the context), Task (what needed explaining), Action (how you simplified it — analogies, visuals), Result (stakeholder understood and made a better decision)."},
            {"question": "Describe a situation where a model you deployed failed in production. What did you do?", "type": "behavioral", "expected_topics": ["ownership", "debugging", "rollback", "post-mortem"], "difficulty": "medium", "sample_answer": "STAR: Describe the failure (data drift, edge case), immediate action (rollback or fallback), root cause analysis, and systemic fix (monitoring, better test coverage)."},
        ],
        "scenario": [
            {"question": "You're asked to build a chatbot for customer support. Walk me through your end-to-end design.", "type": "scenario", "expected_topics": ["RAG", "LLM", "intent detection", "escalation", "evaluation", "latency"], "difficulty": "hard", "sample_answer": "Intent detection → routing → RAG over support docs → LLM response generation → human escalation path → evaluation pipeline. Discuss latency targets, cost optimization, and safety guardrails."},
            {"question": "Your team wants to reduce the cost of LLM API calls by 50%. What approaches would you evaluate?", "type": "scenario", "expected_topics": ["caching", "smaller models", "batching", "quantization", "prompt compression"], "difficulty": "medium", "sample_answer": "Semantic caching for repeated queries, smaller/cheaper models for simple intents, prompt compression techniques, batching requests, and distilling a smaller task-specific model."},
        ],
    },
    "ML Engineer": {
        "technical": [
            {"question": "What is the difference between batch processing and online learning in ML systems?", "type": "conceptual", "expected_topics": ["batch", "online", "streaming", "model updates"], "difficulty": "medium", "sample_answer": "Batch: train on accumulated data periodically. Online: update model incrementally with each new example. Online learning suits rapidly changing distributions; batch is simpler and more stable."},
            {"question": "Explain model versioning and how you manage model artifacts in a production system.", "type": "technical", "expected_topics": ["MLflow", "model registry", "versioning", "artifacts", "rollback"], "difficulty": "medium", "sample_answer": "Use a model registry (MLflow, SageMaker Registry) to track version, metrics, and lineage. Tag production vs staging. Automate promotion based on evaluation thresholds. Always maintain a previous version for rollback."},
            {"question": "Walk me through designing a feature store for a real-time recommendation system.", "type": "problem-solving", "expected_topics": ["feature store", "low-latency", "point-in-time correctness", "training-serving skew"], "difficulty": "hard", "sample_answer": "Dual storage: offline (S3/warehouse) for training, online (Redis/DynamoDB) for serving. Point-in-time correct lookups for training. Feature transforms computed offline and served online to avoid skew. TTL-based freshness for real-time features."},
            {"question": "How do you detect and handle data drift in production ML?", "type": "technical", "expected_topics": ["PSI", "KL divergence", "monitoring", "alerts", "retraining"], "difficulty": "hard", "sample_answer": "Monitor input feature distributions using PSI or KL divergence. Track prediction distribution shifts. Set threshold alerts. Automate retraining triggers when drift exceeds thresholds. Shadow mode for new model validation."},
        ],
        "behavioral": [
            {"question": "Tell me about a time you improved the performance of an ML model significantly.", "type": "behavioral", "expected_topics": ["feature engineering", "hyperparameter tuning", "architecture choice", "data quality"], "difficulty": "medium", "sample_answer": "STAR: describe the baseline, what analysis revealed the bottleneck (data quality, features, model architecture), changes made, and the quantified improvement."},
            {"question": "Describe a time you had to balance model accuracy with latency/cost constraints.", "type": "behavioral", "expected_topics": ["trade-offs", "stakeholder management", "quantization", "model pruning"], "difficulty": "medium", "sample_answer": "STAR: explain the business constraint, technical options evaluated (distillation, quantization, model selection), the decision made, and the outcome."},
        ],
        "scenario": [
            {"question": "Design a system to automatically retrain and deploy an ML model when performance degrades.", "type": "scenario", "expected_topics": ["monitoring", "drift detection", "CI/CD", "evaluation gate", "shadow deployment"], "difficulty": "hard", "sample_answer": "Monitoring layer detects drift → triggers retraining pipeline → auto-evaluation against holdout → if metrics pass gate → shadow deployment → gradual rollout via canary → full promotion."},
            {"question": "A new dataset has 30% missing values in a key feature. How do you handle it?", "type": "scenario", "expected_topics": ["imputation", "indicator variable", "model-based imputation", "business context"], "difficulty": "medium", "sample_answer": "First understand why it's missing (MAR/MCAR/MNAR). Add a missingness indicator. Consider median/mode imputation, KNN, or model-based (MICE). Never blindly impute without understanding the source."},
        ],
    },
    "Data Scientist": {
        "technical": [
            {"question": "Explain the bias-variance trade-off and how it guides model selection.", "type": "conceptual", "expected_topics": ["bias", "variance", "underfitting", "overfitting", "regularization"], "difficulty": "medium", "sample_answer": "High bias = underfitting (model too simple). High variance = overfitting (too complex). Use cross-validation to diagnose; regularization, more data, or ensembles to fix."},
            {"question": "When would you use A/B testing vs multi-armed bandits?", "type": "technical", "expected_topics": ["A/B test", "MAB", "exploration", "exploitation", "regret"], "difficulty": "hard", "sample_answer": "A/B: clean comparison, sufficient traffic, fixed experiment duration. MAB: dynamically allocate traffic to better-performing variants, minimizing regret — better when stopping early has business value."},
            {"question": "Walk me through a complete EDA you would do on a new dataset.", "type": "problem-solving", "expected_topics": ["shape", "dtypes", "nulls", "distributions", "correlations", "outliers", "target relationship"], "difficulty": "medium", "sample_answer": "Shape, dtypes, null counts → distributions (histograms, box plots) → correlation matrix → target variable analysis → feature-target relationships → outlier detection → data quality report."},
            {"question": "What is causal inference and how does it differ from predictive modeling?", "type": "conceptual", "expected_topics": ["causation", "correlation", "RCT", "do-calculus", "confounders"], "difficulty": "hard", "sample_answer": "Predictive modeling: maximize predictive accuracy regardless of mechanism. Causal inference: estimate the effect of interventions, controlling for confounders. Requires structural assumptions or randomization."},
        ],
        "behavioral": [
            {"question": "Tell me about a data science project that failed and what you learned.", "type": "behavioral", "expected_topics": ["failure", "learning", "iteration", "communication"], "difficulty": "medium", "sample_answer": "STAR: describe the project, what went wrong (bad data, wrong framing, stakeholder misalignment), what you learned, and what you'd do differently."},
            {"question": "How do you present statistical findings to a non-technical audience?", "type": "behavioral", "expected_topics": ["communication", "visualization", "storytelling", "uncertainty"], "difficulty": "medium", "sample_answer": "Lead with the business question and answer. Use visualizations over tables. State the key finding in one sentence. Quantify uncertainty in plain language ('we're 95% confident the effect is between X and Y')."},
        ],
        "scenario": [
            {"question": "You notice your churn model has high accuracy but the business says it's not useful. What happened?", "type": "scenario", "expected_topics": ["class imbalance", "precision-recall", "business metric", "cost-sensitive learning"], "difficulty": "hard", "sample_answer": "Likely class imbalance — high accuracy from predicting majority class (non-churn). Reframe with recall/precision on the churn class. Align model threshold with business cost of false negatives vs false positives."},
            {"question": "Design an experiment to measure the impact of a new recommendation algorithm on revenue.", "type": "scenario", "expected_topics": ["A/B test", "power analysis", "metrics", "SUTVA", "novelty effect"], "difficulty": "hard", "sample_answer": "Define primary metric (revenue per user), secondary (CTR, retention). Power analysis for sample size. Random assignment by user. Run for 2+ weeks (account for novelty effect). Check SUTVA. Analyze with correct statistical test."},
        ],
    },
    "Full Stack Developer": {
        "technical": [
            {"question": "Explain the difference between REST and GraphQL APIs.", "type": "conceptual", "expected_topics": ["REST", "GraphQL", "over-fetching", "under-fetching", "schema"], "difficulty": "medium", "sample_answer": "REST: fixed endpoints returning fixed shapes. GraphQL: single endpoint, client specifies exact data shape, prevents over/under-fetching. GraphQL better for complex, rapidly changing front-ends; REST simpler and more cacheable."},
            {"question": "How does the browser critical rendering path work?", "type": "technical", "expected_topics": ["DOM", "CSSOM", "render tree", "layout", "paint", "JavaScript blocking"], "difficulty": "hard", "sample_answer": "HTML → DOM. CSS → CSSOM. Merge → Render Tree → Layout (positions/sizes) → Paint → Composite. JS blocks parsing unless async/defer. Optimize by minimizing render-blocking resources."},
            {"question": "What are web accessibility (WCAG) best practices and why do they matter?", "type": "conceptual", "expected_topics": ["ARIA", "semantic HTML", "color contrast", "keyboard navigation", "screen readers"], "difficulty": "medium", "sample_answer": "Use semantic HTML elements (header, nav, main), ARIA attributes for dynamic content, sufficient color contrast (4.5:1), keyboard navigation support, alt text for images. Accessibility benefits all users and is legally required in many jurisdictions."},
            {"question": "Describe how you would optimize a slow React application.", "type": "problem-solving", "expected_topics": ["profiler", "useMemo", "useCallback", "code splitting", "lazy loading", "virtualization"], "difficulty": "hard", "sample_answer": "Profile first with React DevTools. Fix unnecessary re-renders with memo/useCallback/useMemo. Code-split with lazy() + Suspense. Virtualize long lists. Optimize images. Analyze bundle with webpack-bundle-analyzer."},
        ],
        "behavioral": [
            {"question": "Tell me about a time you had to make a difficult technical decision under time pressure.", "type": "behavioral", "expected_topics": ["prioritization", "trade-offs", "communication", "outcome"], "difficulty": "medium", "sample_answer": "STAR: describe the context, the options, how you evaluated trade-offs quickly, the decision, and whether it worked out."},
            {"question": "Describe a time you improved the performance or quality of a legacy codebase.", "type": "behavioral", "expected_topics": ["refactoring", "testing", "incremental", "team collaboration"], "difficulty": "medium", "sample_answer": "STAR: describe the codebase state, your approach (strangler fig pattern, adding tests first), changes made, metrics improved."},
        ],
        "scenario": [
            {"question": "Design a URL shortener service (like bit.ly) with 10M+ redirects per day.", "type": "scenario", "expected_topics": ["hashing", "database", "CDN", "cache", "analytics", "rate limiting"], "difficulty": "hard", "sample_answer": "Hash URL to short code. Store in KV store (Redis) for fast lookups. DB for persistence. CDN for global low-latency redirects. Cache hit rate target >99%. Rate limiting for abuse. Async analytics writes."},
            {"question": "How would you implement real-time notifications in a web application?", "type": "scenario", "expected_topics": ["WebSockets", "SSE", "polling", "pub-sub", "scalability"], "difficulty": "medium", "sample_answer": "SSE for one-way (server → client) notifications. WebSockets for bidirectional. Use a message broker (Redis pub/sub, Kafka) to fan out. Scale with sticky sessions or shared state. Fall back to long-polling for reliability."},
        ],
    },
    "Backend Developer": {
        "technical": [
            {"question": "What are the ACID properties of database transactions?", "type": "conceptual", "expected_topics": ["atomicity", "consistency", "isolation", "durability"], "difficulty": "medium", "sample_answer": "Atomicity: all or nothing. Consistency: valid state transitions. Isolation: concurrent transactions don't interfere. Durability: committed data persists through failures. These are enforced by the database engine."},
            {"question": "Explain the difference between SQL and NoSQL databases and when to choose each.", "type": "conceptual", "expected_topics": ["schema", "ACID", "scalability", "CAP", "document", "key-value"], "difficulty": "medium", "sample_answer": "SQL: structured schema, ACID, relational integrity — for financial, transactional systems. NoSQL: flexible schema, horizontal scale, eventual consistency — for high write throughput, unstructured data, or specific access patterns."},
            {"question": "How do you secure a REST API?", "type": "technical", "expected_topics": ["JWT", "OAuth", "HTTPS", "rate limiting", "input validation", "OWASP"], "difficulty": "medium", "sample_answer": "HTTPS everywhere. JWT/OAuth for auth. Input validation and parameterized queries (no SQL injection). Rate limiting. CORS policy. Secrets in env vars, not code. Follow OWASP API Security Top 10."},
            {"question": "What is the N+1 query problem and how do you fix it?", "type": "problem-solving", "expected_topics": ["ORM", "eager loading", "lazy loading", "JOIN", "select_related"], "difficulty": "medium", "sample_answer": "N+1: fetching N parent records then making N separate queries for children. Fix with JOIN (one query) or ORM eager loading (selectinload, prefetch_related). Always check generated SQL in development."},
        ],
        "behavioral": [
            {"question": "Tell me about a production incident you handled. What was your process?", "type": "behavioral", "expected_topics": ["incident response", "communication", "root cause", "post-mortem"], "difficulty": "medium", "sample_answer": "STAR: describe the incident, your role (on-call, debugging), immediate mitigation, root cause analysis, post-mortem actions (monitoring, tests, docs)."},
            {"question": "How do you approach code reviews as both reviewer and reviewee?", "type": "behavioral", "expected_topics": ["constructive feedback", "standards", "learning", "efficiency"], "difficulty": "easy", "sample_answer": "Reviewer: focus on correctness, security, maintainability, not style (that's for linters). Be constructive. Reviewee: respond to all comments, don't take it personally, ask for clarification."},
        ],
        "scenario": [
            {"question": "Design a rate limiter for an API that handles 100k requests per second.", "type": "scenario", "expected_topics": ["token bucket", "Redis", "sliding window", "distributed", "latency"], "difficulty": "hard", "sample_answer": "Token bucket or sliding window counter in Redis (atomic INCR + EXPIRE). Distributed: use Redis cluster. Local fallback counter for Redis unavailability. Respond with 429 + Retry-After header. Consider per-user and per-IP limits."},
            {"question": "A database query that used to take 50ms is now taking 5 seconds. How do you diagnose it?", "type": "scenario", "expected_topics": ["EXPLAIN", "indexes", "table growth", "locks", "query plan"], "difficulty": "hard", "sample_answer": "Run EXPLAIN/EXPLAIN ANALYZE. Check if index exists and is being used. Check table row count growth. Look for lock contention. Review recent schema changes. Check for parameter sniffing (prepared statement plan cache)."},
        ],
    },
    "Cloud Engineer": {
        "technical": [
            {"question": "Explain the shared responsibility model in cloud security.", "type": "conceptual", "expected_topics": ["provider responsibility", "customer responsibility", "data security", "IAM"], "difficulty": "medium", "sample_answer": "Provider: physical infrastructure, hypervisor, managed services security. Customer: IAM configuration, data encryption, network security groups, application security, OS patching (for IaaS)."},
            {"question": "What is Infrastructure as Code (IaC) and what are its benefits?", "type": "conceptual", "expected_topics": ["Terraform", "CloudFormation", "reproducibility", "version control", "drift detection"], "difficulty": "medium", "sample_answer": "IaC defines infrastructure in code (Terraform, CloudFormation, Pulumi). Benefits: reproducible environments, version-controlled changes, code review for infra, automated provisioning, drift detection."},
            {"question": "How would you design a highly available architecture on AWS for a web application?", "type": "problem-solving", "expected_topics": ["multi-AZ", "load balancer", "auto-scaling", "RDS Multi-AZ", "CDN", "Route53"], "difficulty": "hard", "sample_answer": "Multi-AZ EC2 ASG behind ALB. RDS Multi-AZ. S3 for static assets. CloudFront CDN. Route53 health checks. ElastiCache for sessions. Cross-region replication for DR. Target 99.99% SLA."},
            {"question": "What is Kubernetes and why is it used for container orchestration?", "type": "conceptual", "expected_topics": ["pods", "deployments", "services", "scheduling", "self-healing", "scaling"], "difficulty": "medium", "sample_answer": "K8s automates deployment, scaling, and management of containerized applications. Key features: declarative config, self-healing (restart failed pods), horizontal pod autoscaling, service discovery, rolling updates."},
        ],
        "behavioral": [
            {"question": "Tell me about a cloud cost optimization you implemented.", "type": "behavioral", "expected_topics": ["cost analysis", "right-sizing", "reserved instances", "savings"], "difficulty": "medium", "sample_answer": "STAR: describe the cost problem, analysis done (cost explorer, tagging), options evaluated (reserved instances, spot, right-sizing), savings achieved."},
            {"question": "Describe a situation where you improved system reliability.", "type": "behavioral", "expected_topics": ["SLA", "monitoring", "alerting", "redundancy", "runbooks"], "difficulty": "medium", "sample_answer": "STAR: describe the reliability issue, what you analyzed (error budget, SLO burn rate), changes made (circuit breakers, retries, alerting), and the improved SLA."},
        ],
        "scenario": [
            {"question": "Design a disaster recovery strategy for a critical business application.", "type": "scenario", "expected_topics": ["RTO", "RPO", "backup", "cross-region", "failover", "testing"], "difficulty": "hard", "sample_answer": "Define RTO/RPO targets. Warm standby or pilot light in secondary region. Cross-region S3 replication. DB read replicas promoted on failover. Route53 health check-based failover. Regular DR drills. Document runbooks."},
            {"question": "You need to migrate a monolithic application to microservices in the cloud. What is your approach?", "type": "scenario", "expected_topics": ["strangler fig", "domain decomposition", "API gateway", "service mesh", "observability"], "difficulty": "hard", "sample_answer": "Strangler fig pattern: incrementally extract services. Start with least-coupled, highest-value domains. API gateway for routing. Introduce service mesh for observability and traffic control. Don't rewrite everything at once."},
        ],
    },
    "DevOps Engineer": {
        "technical": [
            {"question": "What is the difference between continuous integration, delivery, and deployment?", "type": "conceptual", "expected_topics": ["CI", "CD", "automation", "testing", "release"], "difficulty": "medium", "sample_answer": "CI: automatically build and test on every commit. CD (Delivery): automatically prepare releasable artifacts, manual approval for production. CD (Deployment): fully automated push to production on every green build."},
            {"question": "Explain GitOps and how it differs from traditional CI/CD.", "type": "conceptual", "expected_topics": ["GitOps", "declarative", "ArgoCD", "Flux", "reconciliation"], "difficulty": "hard", "sample_answer": "GitOps: Git is the single source of truth for infrastructure and app config. A reconciliation loop (ArgoCD, Flux) continuously applies the desired state from Git to the cluster. No imperative scripts; audit trail via Git history."},
            {"question": "How do you implement zero-downtime deployments?", "type": "technical", "expected_topics": ["blue-green", "canary", "rolling update", "feature flags", "database migrations"], "difficulty": "hard", "sample_answer": "Rolling updates (gradual pod replacement), blue-green (switch traffic atomically), or canary (gradual traffic shift). Handle DB migrations with backward-compatible changes first. Use feature flags for risky changes. Health checks before traffic."},
            {"question": "What metrics would you monitor for a production microservices application?", "type": "technical", "expected_topics": ["RED", "USE", "latency", "error rate", "saturation", "traces"], "difficulty": "medium", "sample_answer": "RED method: Rate (requests/sec), Errors (error %), Duration (latency p50/p99). USE: Utilization, Saturation, Errors for infrastructure. Add distributed traces (Jaeger, Zipkin), structured logs, and synthetic monitoring."},
        ],
        "behavioral": [
            {"question": "Tell me about a major production outage you resolved. What was your role?", "type": "behavioral", "expected_topics": ["incident response", "communication", "MTTR", "post-mortem"], "difficulty": "medium", "sample_answer": "STAR: the alert, your actions (triage, mitigation, communication to stakeholders), root cause fix, MTTR achieved, and post-mortem improvements."},
            {"question": "How do you handle pushback from developers on DevOps practices like testing or security gates?", "type": "behavioral", "expected_topics": ["influence", "collaboration", "data-driven", "developer experience"], "difficulty": "medium", "sample_answer": "Show the cost of the current approach (incidents, security issues). Make the right path the easy path (fast tests, self-service security scanning). Involve devs in tooling decisions. Start with a pilot team."},
        ],
        "scenario": [
            {"question": "Design a CI/CD pipeline for a microservices application with 20 services.", "type": "scenario", "expected_topics": ["parallel builds", "testing pyramid", "image registry", "environment promotion", "rollback"], "difficulty": "hard", "sample_answer": "Monorepo or polyrepo with change detection. Parallel pipeline per service. Unit → integration → contract tests. Build and push Docker image with commit SHA tag. Promote through dev → staging → prod. Automated rollback on failed health checks."},
            {"question": "Your Kubernetes cluster is running out of resources and pods are being OOM killed. How do you fix it?", "type": "scenario", "expected_topics": ["resource limits", "requests", "HPA", "VPA", "node scaling", "profiling"], "difficulty": "hard", "sample_answer": "Set correct resource requests/limits based on profiling. Use HPA for stateless services. VPA for right-sizing. Cluster autoscaler for node scaling. Check for memory leaks. Review pod disruption budgets. Consider namespace resource quotas."},
        ],
    },
}

# Normalize role name for lookup
_ROLE_ALIASES: dict[str, str] = {
    "ai engineer": "AI Engineer",
    "ml engineer": "ML Engineer",
    "machine learning engineer": "ML Engineer",
    "data scientist": "Data Scientist",
    "full stack developer": "Full Stack Developer",
    "fullstack developer": "Full Stack Developer",
    "full stack engineer": "Full Stack Developer",
    "backend developer": "Backend Developer",
    "backend engineer": "Backend Developer",
    "cloud engineer": "Cloud Engineer",
    "cloud architect": "Cloud Engineer",
    "devops engineer": "DevOps Engineer",
    "devops": "DevOps Engineer",
    "site reliability engineer": "DevOps Engineer",
    "sre": "DevOps Engineer",
}


def _get_interview_fallback(role: str, min_technical: int = 3, min_behavioral: int = 2, min_scenario: int = 2) -> dict:
    """Return a structured fallback interview question set for the given role."""
    role_key = role.lower().strip()
    canonical_role = _ROLE_ALIASES.get(role_key)

    # Fuzzy match if no direct alias
    if not canonical_role:
        for alias, canonical in _ROLE_ALIASES.items():
            if alias in role_key or role_key in alias:
                canonical_role = canonical
                break

    bank = _INTERVIEW_BANK.get(canonical_role or "", _INTERVIEW_BANK["AI Engineer"])

    technical_q = random.sample(bank["technical"], min(min_technical, len(bank["technical"])))
    behavioral_q = random.sample(bank["behavioral"], min(min_behavioral, len(bank["behavioral"])))
    scenario_q = random.sample(bank["scenario"], min(min_scenario, len(bank["scenario"])))

    return {
        "role": role,
        "sections": [
            {"category": "Technical", "questions": technical_q},
            {"category": "Behavioral", "questions": behavioral_q},
            {"category": "Scenario-Based", "questions": scenario_q},
        ],
        "tips": [
            "Use the STAR method (Situation, Task, Action, Result) for behavioral questions.",
            "Think out loud for technical problems — interviewers want to see your reasoning process.",
            "Ask clarifying questions before diving into system design problems.",
            "Quantify your impact in behavioral answers (e.g., 'reduced latency by 40%').",
            "Research the company's tech stack and recent engineering blog posts.",
        ],
    }


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
        data = _extract_json(raw)
        # Validate structure
        if not isinstance(data.get("questions"), list) or len(data["questions"]) == 0:
            raise ValueError("No questions in response")
        return data
    except Exception:
        # Use deterministic fallback bank with real questions
        questions = _get_fallback_questions(topic, num_questions)
        return {"topic": topic, "difficulty": difficulty, "questions": questions}


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
    {{"category": "Behavioral", "questions": [{{"question": "Tell me about a challenge", "type": "behavioral", "expected_topics": ["teamwork"], "difficulty": "medium", "sample_answer": "Use STAR method"}}]}},
    {{"category": "Scenario-Based", "questions": [{{"question": "Scenario question", "type": "scenario", "expected_topics": ["design"], "difficulty": "medium", "sample_answer": "Walk through your approach"}}]}}
  ],
  "tips": ["Tip 1", "Tip 2"]
}}"""
    try:
        raw = await get_ai_response(prompt, SYSTEM_MENTOR, temperature=0.5)
        data = _extract_json(raw)
        # Validate structure
        if not isinstance(data.get("sections"), list) or len(data["sections"]) == 0:
            raise ValueError("No sections in response")
        return data
    except Exception:
        # Use deterministic fallback bank with role-specific questions
        return _get_interview_fallback(role, min_technical=3, min_behavioral=2, min_scenario=2)


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
