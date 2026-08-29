"""Analytics, Quiz, Resume, and Career Readiness routes."""
import json
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, case, Integer, cast

from app.db.session import get_db
from app.models.models import User, LearnerProfile, QuizResult, ProgressLog, Roadmap, Milestone, LearningStreak
from app.schemas.schemas import (
    SkillGapRequest, SkillGapReport, ProgressLogCreate, ProgressLogOut,
    QuizRequest, QuizSubmit, CareerReadinessOut, WeeklyPlanOut, ResumeAnalysisResult
)
from app.core.deps import get_current_user
from app.ai.ai_service import (
    analyze_skill_gap as ai_analyze_skill_gap,
    calculate_career_readiness, generate_quiz,
    generate_weekly_plan, analyze_resume, generate_mock_interview_questions,
    generate_skill_gap_explanation, generate_whatif_explanation,
)
from app.services.mastery_service import (
    get_skill_gap_for_user, get_mastery_map, apply_quiz_result,
    get_next_best_action, record_adaptation,
)
from app.services.skill_graph import (
    build_mastery_map_from_skills, calculate_skill_gap, list_known_roles,
)

router = APIRouter(prefix="/analytics", tags=["Analytics & AI Tools"])


# ─── Skill Gap ────────────────────────────────────────────────────────────────

@router.post("/skill-gap", response_model=dict)
async def skill_gap_analysis(
    payload: SkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Deterministic skill-gap analysis using the RoleSkillGraph.
    AI is used only to generate human-readable explanation text —
    all scores are calculated deterministically.
    """
    # Build mastery map: DB mastery rows take precedence;
    # fill unknowns from the payload's current_skills list.
    mastery_map = await get_mastery_map(db, current_user.id)
    # Merge payload skills (self-reported) for skills not yet in DB
    from app.services.skill_graph import build_mastery_map_from_skills, normalize_skill
    payload_mastery = build_mastery_map_from_skills(payload.current_skills, "intermediate")
    for skill, score in payload_mastery.items():
        if skill not in mastery_map:
            mastery_map[skill] = score

    gap_result = calculate_skill_gap(payload.target_role, mastery_map)

    # Build structured response
    result = {
        "target_role": gap_result.target_role,
        "required_skills": [
            {
                "skill": item.skill,
                "current_mastery": item.current_mastery,
                "gap_score": item.gap_score,
                "status": item.status,
                "importance": item.required_importance,
                "prerequisites": item.prerequisites,
                "prerequisites_met": item.prerequisites_met,
            }
            for item in gap_result.required_skills
        ],
        "overall_gap_pct": gap_result.overall_gap_pct,
        "career_readiness_pct": gap_result.career_readiness_pct,
        "priority_skills": gap_result.priority_skills,
        "strong_skills": gap_result.strong_skills,
        "developing_skills": gap_result.developing_skills,
        "gap_skills": gap_result.gap_skills,
        # Legacy fields kept for frontend compatibility
        "current_skills": payload.current_skills,
        "missing_skills": gap_result.gap_skills,
        "gap_percentage": gap_result.overall_gap_pct,
        "skill_scores": {item.skill: item.current_mastery for item in gap_result.required_skills},
        "recommendations": [
            f"Focus on {s} — it is your highest-priority gap for {gap_result.target_role}"
            for s in gap_result.priority_skills[:3]
        ],
    }

    # Persist to profile
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.skill_gap_report = json.dumps(result)
        await db.commit()

    return result


@router.get("/skill-gap", response_model=dict)
async def get_skill_gap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current skill gap for the user's target role from their profile."""
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile or not profile.career_goal:
        raise HTTPException(status_code=404, detail="Complete your profile with a career goal first")

    gap_result = await get_skill_gap_for_user(
        db, current_user.id, profile.career_goal, profile.experience_level or "beginner"
    )

    result = {
        "target_role": gap_result.target_role,
        "required_skills": [
            {
                "skill": item.skill,
                "current_mastery": item.current_mastery,
                "gap_score": item.gap_score,
                "status": item.status,
                "importance": item.required_importance,
                "prerequisites": item.prerequisites,
                "prerequisites_met": item.prerequisites_met,
            }
            for item in gap_result.required_skills
        ],
        "overall_gap_pct": gap_result.overall_gap_pct,
        "career_readiness_pct": gap_result.career_readiness_pct,
        "priority_skills": gap_result.priority_skills,
        "strong_skills": gap_result.strong_skills,
        "developing_skills": gap_result.developing_skills,
        "gap_skills": gap_result.gap_skills,
        "skill_scores": {item.skill: item.current_mastery for item in gap_result.required_skills},
        "gap_percentage": gap_result.overall_gap_pct,
        "missing_skills": gap_result.gap_skills,
        "recommendations": [
            f"Focus on {s} — it is your highest-priority gap for {gap_result.target_role}"
            for s in gap_result.priority_skills[:3]
        ],
    }
    return result


@router.get("/roles", response_model=list[str])
async def list_roles(_: User = Depends(get_current_user)):
    """List all supported target roles."""
    return list_known_roles()


@router.get("/next-best-action", response_model=list[dict])
async def next_best_action(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the top 3 learning actions based on current skill mastery gaps."""
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile or not profile.career_goal:
        return []
    return await get_next_best_action(
        db, current_user.id, profile.career_goal, profile.weekly_hours or 10
    )


@router.get("/mastery", response_model=dict)
async def get_mastery(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current skill mastery map for the user."""
    mastery_map = await get_mastery_map(db, current_user.id)
    return {"mastery": mastery_map}


@router.get("/explain/{skill}", response_model=dict)
async def explain_recommendation(
    skill: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a grounded, personalized explanation for why a skill is recommended.
    The explanation references actual mastery scores — not a generic statement.
    """
    from app.ai.ai_service import generate_skill_gap_explanation
    from app.services.skill_graph import normalize_skill

    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    target_role = profile.career_goal if profile else "your target role"

    mastery_map = await get_mastery_map(db, current_user.id)
    canonical = normalize_skill(skill)
    current_mastery = mastery_map.get(canonical, 0.0)

    gap_result = await get_skill_gap_for_user(
        db, current_user.id, target_role, profile.experience_level if profile else "beginner"
    )

    item = next((i for i in gap_result.required_skills if i.skill == canonical), None)
    prerequisites = item.prerequisites if item else []

    explanation = await generate_skill_gap_explanation(
        skill=canonical,
        current_mastery=current_mastery,
        target_role=target_role,
        prerequisites=prerequisites,
        strong_skills=gap_result.strong_skills,
    )

    return {
        "skill": canonical,
        "current_mastery": round(current_mastery, 1),
        "target_role": target_role,
        "prerequisites": prerequisites,
        "explanation": explanation,
        "status": item.status if item else "unknown",
        "importance": item.required_importance if item else 0.5,
    }


# ─── Career Readiness ─────────────────────────────────────────────────────────

@router.get("/career-readiness", response_model=dict)
async def get_career_readiness(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")

    # Count milestones
    milestone_stats = await db.execute(
        select(
            sqlfunc.count(Milestone.id).label("total"),
            sqlfunc.sum(case((Milestone.is_completed == True, 1), else_=0)).label("completed"),
        )
        .join(Roadmap)
        .where(Roadmap.user_id == current_user.id)
    )
    stats = milestone_stats.one()

    # Quiz avg
    quiz_avg = await db.execute(
        select(sqlfunc.avg(QuizResult.score)).where(QuizResult.user_id == current_user.id)
    )
    avg_score = quiz_avg.scalar() or 0

    streak_result = await db.execute(
        select(LearningStreak).where(LearningStreak.user_id == current_user.id)
    )
    streak = streak_result.scalar_one_or_none()

    progress_data = {
        "milestones_completed": stats.completed or 0,
        "total_milestones": stats.total or 0,
        "quiz_avg_score": round(avg_score, 1),
        "days_active": streak.total_days_active if streak else 0,
    }

    profile_dict = {
        "career_goal": profile.career_goal,
        "current_skills": json.loads(profile.current_skills) if isinstance(profile.current_skills, str) else (profile.current_skills or []),
        "completed_courses": json.loads(profile.completed_courses) if isinstance(profile.completed_courses, str) else (profile.completed_courses or []),
        "experience_level": profile.experience_level,
    }

    try:
        result = await calculate_career_readiness(profile_dict, progress_data)
    except Exception:
        # Double-fallback: deterministic result if AI service is entirely unavailable
        score = min(100.0, (progress_data["milestones_completed"] / max(1, progress_data["total_milestones"])) * 100)
        result = {
            "score": round(score, 1),
            "breakdown": {
                "skills": round(score, 1),
                "projects": 0,
                "certifications": 0,
                "assessments": progress_data["quiz_avg_score"],
                "consistency": 50,
            },
            "weak_areas": [],
            "strong_areas": [],
            "suggestions": ["Keep completing milestones to improve your career readiness score"],
            "interview_ready": score >= 80,
            "estimated_months_to_ready": max(1, int((100 - score) / 10)),
        }

    # Update score in profile
    profile.career_readiness_score = result.get("score", 0)
    await db.commit()

    return result

@router.get("/dashboard")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    roadmaps_result = await db.execute(
        select(Roadmap).where(Roadmap.user_id == current_user.id, Roadmap.status == "active")
    )
    roadmaps = roadmaps_result.scalars().all()

    streak_result = await db.execute(
        select(LearningStreak).where(LearningStreak.user_id == current_user.id)
    )
    streak = streak_result.scalar_one_or_none()

    quiz_count = await db.execute(
        select(sqlfunc.count(QuizResult.id)).where(QuizResult.user_id == current_user.id)
    )
    quiz_avg = await db.execute(
        select(sqlfunc.avg(QuizResult.score)).where(QuizResult.user_id == current_user.id)
    )

    milestone_stats = await db.execute(
        select(
            sqlfunc.count(Milestone.id).label("total"),
            sqlfunc.sum(case((Milestone.is_completed == True, 1), else_=0)).label("completed"),
        )
        .join(Roadmap)
        .where(Roadmap.user_id == current_user.id)
    )
    m_stats = milestone_stats.one()

    return {
        "profile": {
            "career_goal": profile.career_goal if profile else None,
            "career_readiness_score": profile.career_readiness_score if profile else 0,
            "current_skills": (json.loads(profile.current_skills) if isinstance(profile.current_skills, str) else (profile.current_skills or [])) if profile else [],
            "experience_level": profile.experience_level if profile else "beginner",
        },
        "roadmaps": [
            {"id": str(r.id), "title": r.title, "completion_percentage": r.completion_percentage}
            for r in roadmaps
        ],
        "streak": {
            "current_streak": streak.current_streak if streak else 0,
            "longest_streak": streak.longest_streak if streak else 0,
            "total_days_active": streak.total_days_active if streak else 0,
        },
        "milestones": {
            "total": m_stats.total or 0,
            "completed": m_stats.completed or 0,
            "percentage": round(((m_stats.completed or 0) / (m_stats.total or 1)) * 100, 1),
        },
        "quizzes": {
            "count": quiz_count.scalar() or 0,
            "avg_score": round(quiz_avg.scalar() or 0, 1),
        },
    }


# ─── Quiz ─────────────────────────────────────────────────────────────────────

@router.post("/quiz/generate", response_model=dict)
async def generate_quiz_endpoint(
    payload: QuizRequest,
    current_user: User = Depends(get_current_user),
):
    return await generate_quiz(payload.topic, payload.difficulty, payload.num_questions)


@router.post("/quiz/submit", response_model=dict)
async def submit_quiz(
    payload: QuizSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate quiz answers, save result, and update skill mastery deterministically."""
    questions = payload.questions.get("questions", [])
    answers = payload.answers
    correct = 0
    feedback_items = []

    for q in questions:
        qid = q.get("id")
        correct_ans = q.get("correct_answer")
        user_ans = answers.get(qid)
        if user_ans == correct_ans:
            correct += 1
        else:
            feedback_items.append(f"Q: {q.get('question')} — Correct: {correct_ans}. {q.get('explanation', '')}")

    score = (correct / len(questions)) * 100 if questions else 0
    score_rounded = round(score, 1)

    quiz_result = QuizResult(
        user_id=current_user.id,
        topic=payload.topic,
        score=score_rounded,
        questions_json=json.dumps(payload.questions),
        feedback="\n".join(feedback_items) if feedback_items else "All correct!",
    )
    db.add(quiz_result)
    await db.flush()

    # ── Deterministic mastery update ──────────────────────────────────────────
    old_mastery, new_mastery = await apply_quiz_result(
        db, current_user.id, payload.topic, score_rounded
    )

    # Record adaptation event if mastery changed significantly (>5 points)
    mastery_delta = new_mastery - old_mastery
    adaptation_explanation = None
    if abs(mastery_delta) > 5:
        # Find the user's active roadmap
        roadmap_result = await db.execute(
            select(Roadmap)
            .where(Roadmap.user_id == current_user.id, Roadmap.status == "active")
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        roadmap = roadmap_result.scalar_one_or_none()
        if roadmap:
            direction = "increased" if mastery_delta > 0 else "decreased"
            action = (
                f"Quiz score {score_rounded:.0f}% on {payload.topic}: "
                f"mastery {direction} from {old_mastery:.0f}% to {new_mastery:.0f}%"
            )
            await record_adaptation(
                db=db,
                user_id=current_user.id,
                roadmap_id=roadmap.id,
                trigger="quiz_result",
                skill=payload.topic,
                old_mastery=old_mastery,
                new_mastery=new_mastery,
                action_taken=action,
            )
            # Generate AI explanation for the adaptation (non-blocking)
            try:
                from app.ai.ai_service import generate_adaptation_explanation
                profile_result = await db.execute(
                    select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
                )
                profile = profile_result.scalar_one_or_none()
                target_role = profile.career_goal if profile else "your target role"
                adaptation_explanation = await generate_adaptation_explanation(
                    skill=payload.topic,
                    old_mastery=old_mastery,
                    new_mastery=new_mastery,
                    action_taken=action,
                    target_role=target_role,
                )
            except Exception:
                adaptation_explanation = action

    await db.commit()

    return {
        "score": score_rounded,
        "correct": correct,
        "total": len(questions),
        "feedback": feedback_items,
        "passed": score >= 60,
        "mastery_update": {
            "skill": payload.topic,
            "old_mastery": round(old_mastery, 1),
            "new_mastery": round(new_mastery, 1),
            "delta": round(mastery_delta, 1),
        },
        "adaptation": {
            "triggered": abs(mastery_delta) > 5,
            "explanation": adaptation_explanation,
        } if abs(mastery_delta) > 5 else {"triggered": False, "explanation": None},
    }


# ─── Weekly Plan ──────────────────────────────────────────────────────────────

@router.get("/weekly-plan", response_model=dict)
async def get_weekly_plan(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first")

    # Get next incomplete milestone
    next_milestone_result = await db.execute(
        select(Milestone)
        .join(Roadmap)
        .where(Roadmap.user_id == current_user.id, Milestone.is_completed == False)
        .order_by(Milestone.month_number)
        .limit(1)
    )
    next_milestone = next_milestone_result.scalar_one_or_none()
    milestone_dict = None
    if next_milestone:
        milestone_dict = {
            "title": next_milestone.title,
            "topics": next_milestone.topics,
            "estimated_hours": next_milestone.estimated_hours,
        }

    profile_dict = {
        "career_goal": profile.career_goal,
        "weekly_hours": profile.weekly_hours,
        "learning_style": profile.learning_style,
        "current_skills": json.loads(profile.current_skills) if isinstance(profile.current_skills, str) else (profile.current_skills or []),
    }

    try:
        return await generate_weekly_plan(profile_dict, milestone_dict)
    except Exception:
        # Deterministic fallback when AI service is entirely unavailable
        hours = profile.weekly_hours or 10
        minutes_per_day = max(30, (hours * 60) // 5)
        focus = [milestone_dict["title"]] if milestone_dict else [profile.career_goal or "Core topics"]
        return {
            "week_number": 1,
            "goal": f"Progress towards {profile.career_goal or 'your goal'}",
            "total_hours": hours,
            "focus_topics": focus,
            "daily_plans": [
                {
                    "day": day,
                    "tasks": [{"title": "Study session", "type": "study", "duration_minutes": minutes_per_day, "resource": "Course material", "description": f"Review {focus[0]}"}],
                    "total_minutes": minutes_per_day,
                }
                for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
            ],
            "revision_slots": ["Saturday: Review week's topics", "Sunday: Rest or practice project"],
            "assessment": "End-of-week quiz on covered topics",
        }


# ─── Resume Analysis ──────────────────────────────────────────────────────────

@router.post("/resume", response_model=dict)
async def analyze_resume_endpoint(
    file: UploadFile = File(...),
    target_role: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a resume (PDF/TXT/DOCX) for skill extraction and analysis."""
    content = await file.read()

    # Extract text based on file type
    text = ""
    if file.filename.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    elif file.filename.endswith(".pdf"):
        try:
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = " ".join(p.extract_text() or "" for p in reader.pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not parse PDF")
    elif file.filename.endswith(".docx"):
        try:
            import docx, io
            doc = docx.Document(io.BytesIO(content))
            text = " ".join(p.text for p in doc.paragraphs)
        except Exception:
            raise HTTPException(status_code=400, detail="Could not parse DOCX")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")

    result = await analyze_resume(text, target_role)

    # Auto-update profile with extracted skills
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        existing_raw = profile.current_skills
        existing = set(json.loads(existing_raw) if isinstance(existing_raw, str) else (existing_raw or []))
        new_skills = list(existing | set(result.get("extracted_skills", [])))
        profile.current_skills = json.dumps(new_skills)
        profile.resume_text = text[:5000]
        await db.commit()

    return result


# ─── Mock Interview ───────────────────────────────────────────────────────────

@router.post("/mock-interview", response_model=dict)
async def mock_interview(
    role: str,
    difficulty: str = "intermediate",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    skills = json.loads(profile.current_skills) if profile and isinstance(profile.current_skills, str) else (profile.current_skills if profile else [])
    return await generate_mock_interview_questions(role, skills, difficulty)


# ─── Progress Log ─────────────────────────────────────────────────────────────

@router.post("/progress", response_model=ProgressLogOut, status_code=201)
async def log_progress(
    payload: ProgressLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone, date

    log = ProgressLog(user_id=current_user.id, **payload.model_dump())
    db.add(log)

    # Update streak
    streak_result = await db.execute(
        select(LearningStreak).where(LearningStreak.user_id == current_user.id)
    )
    streak = streak_result.scalar_one_or_none()
    if streak:
        today = date.today()
        last = streak.last_activity_date.date() if streak.last_activity_date else None
        if last != today:
            if last and (today - last).days == 1:
                streak.current_streak += 1
            elif last and (today - last).days > 1:
                streak.current_streak = 1
            else:
                streak.current_streak = 1
            streak.total_days_active += 1
            streak.last_activity_date = datetime.now(timezone.utc)
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak

    await db.commit()
    await db.refresh(log)
    return log


@router.post("/whatif", response_model=dict)
async def whatif_simulation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    weekly_hours: Optional[int] = None,
    target_role: Optional[str] = None,
    timeline_months: Optional[int] = None,
    known_skills: Optional[str] = None,   # comma-separated
):
    """
    What-if simulator: show how the roadmap would change under different parameters.
    Pure computation — does NOT change any persisted data until the user confirms.
    """
    from app.services.skill_graph import build_mastery_map_from_skills

    profile_result = await db.execute(        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    # Current params
    current_role = profile.career_goal if profile else "AI Engineer"
    current_hours = profile.weekly_hours if profile else 10
    current_timeline = (profile.target_timeline_months if profile else 12) or 12
    current_mastery = await get_mastery_map(db, current_user.id)

    # Simulated params
    sim_role = target_role or current_role
    sim_hours = weekly_hours or current_hours
    sim_timeline = timeline_months or current_timeline

    # Merge in any extra known skills for the simulation
    sim_mastery = dict(current_mastery)
    if known_skills:
        extra = build_mastery_map_from_skills(
            [s.strip() for s in known_skills.split(",")], "intermediate"
        )
        for skill, score in extra.items():
            if skill not in sim_mastery or sim_mastery[skill] < score:
                sim_mastery[skill] = score

    # Compute gaps
    current_gap = calculate_skill_gap(current_role, current_mastery)
    sim_gap = calculate_skill_gap(sim_role, sim_mastery)

    def estimate_hours(skill_items: list, hours_per_week: int, timeline: int) -> dict:
        """Estimate feasibility given gap items, weekly hours, and timeline in months."""
        total_available = hours_per_week * timeline * 4  # 4 weeks per month
        gap_items = [i for i in skill_items if i.status != "strong"]
        # 1 gap point ≈ 0.5 hours of focused study
        total_gap_hours = sum(i.gap_score * 0.5 for i in gap_items)
        feasible = total_available >= total_gap_hours
        months_needed = round(total_gap_hours / (hours_per_week * 4), 1) if hours_per_week > 0 else 999
        return {
            "total_available_hours": int(total_available),
            "estimated_gap_hours": int(total_gap_hours),
            "feasible_in_timeline": feasible,
            "estimated_months_needed": months_needed,
        }

    current_est = estimate_hours(current_gap.required_skills, current_hours, current_timeline)
    sim_est = estimate_hours(sim_gap.required_skills, sim_hours, sim_timeline)

    # Summarize changes
    changes = []
    if sim_role != current_role:
        changes.append(f"Role changed from '{current_role}' to '{sim_role}'")
    if sim_hours != current_hours:
        direction = "more" if sim_hours > current_hours else "fewer"
        changes.append(f"Study time: {current_hours}h/week → {sim_hours}h/week ({direction} hours)")
    if sim_timeline != current_timeline:
        changes.append(f"Timeline: {current_timeline} months → {sim_timeline} months")
    if known_skills:
        changes.append(f"Added known skills: {known_skills}")
    if not changes:
        changes.append("No parameters changed — showing current state")

    readiness_delta = round(sim_gap.career_readiness_pct - current_gap.career_readiness_pct, 1)
    months_delta = round(sim_est["estimated_months_needed"] - current_est["estimated_months_needed"], 1)

    explanation = await generate_whatif_explanation(
        original_params={"role": current_role, "hours": current_hours, "timeline": current_timeline},
        new_params={"role": sim_role, "hours": sim_hours, "timeline": sim_timeline},
        changes=changes,
    )

    return {
        "simulation_label": "What-If Scenario (not saved — confirm to apply)",
        "changes": changes,
        "current": {
            "role": current_role,
            "weekly_hours": current_hours,
            "timeline_months": current_timeline,
            "career_readiness_pct": current_gap.career_readiness_pct,
            "gap_skills": current_gap.gap_skills,
            "priority_skills": current_gap.priority_skills[:5],
            **current_est,
        },
        "simulated": {
            "role": sim_role,
            "weekly_hours": sim_hours,
            "timeline_months": sim_timeline,
            "career_readiness_pct": sim_gap.career_readiness_pct,
            "gap_skills": sim_gap.gap_skills,
            "priority_skills": sim_gap.priority_skills[:5],
            **sim_est,
        },
        "impact": {
            "readiness_change": readiness_delta,
            "months_change": months_delta,
            "explanation": explanation,
        },
    }


@router.post("/demo-seed", response_model=dict)
async def seed_demo_persona(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    One-click demo persona seed for judges/demos.
    Creates the canonical NeuraLearn demo learner:
      Target: AI Engineer | Timeline: 6mo | 8h/wk
      Python 90, ML 70, Stats 60, Deep Learning 40, GenAI 20, MLOps 10
    Idempotent — safe to call multiple times.
    """
    from app.services.mastery_service import upsert_mastery

    # Update or create profile
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    demo_skills = ["Python", "Machine Learning", "Statistics", "Deep Learning", "Generative AI", "MLOps"]
    demo_skills_json = json.dumps(demo_skills)

    if profile:
        profile.career_goal = "AI Engineer"
        profile.experience_level = "intermediate"
        profile.weekly_hours = 8
        profile.target_timeline_months = 6
        profile.learning_style = "mixed"
        profile.current_skills = demo_skills_json
    else:
        profile = LearnerProfile(
            user_id=current_user.id,
            career_goal="AI Engineer",
            experience_level="intermediate",
            weekly_hours=8,
            target_timeline_months=6,
            learning_style="mixed",
            current_skills=demo_skills_json,
        )
        db.add(profile)
    await db.flush()

    # Seed mastery scores deterministically — demo-canonical values
    demo_mastery = {
        "Python": 90.0,
        "Machine Learning": 70.0,
        "Statistics": 60.0,
        "Deep Learning": 40.0,
        "Generative AI": 20.0,
        "MLOps": 10.0,
    }
    for skill, score in demo_mastery.items():
        await upsert_mastery(db, current_user.id, skill, score, flush=False)

    await db.commit()

    # Recompute gap
    gap_result = await get_skill_gap_for_user(db, current_user.id, "AI Engineer", "intermediate")

    return {
        "message": "Demo persona seeded successfully",
        "profile": {
            "career_goal": "AI Engineer",
            "experience_level": "intermediate",
            "weekly_hours": 8,
            "timeline_months": 6,
        },
        "mastery": demo_mastery,
        "career_readiness_pct": gap_result.career_readiness_pct,
        "gap_skills": gap_result.gap_skills,
        "priority_skills": gap_result.priority_skills[:4],
    }


@router.get("/progress", response_model=list[ProgressLogOut])
async def get_progress_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ProgressLog)
        .where(ProgressLog.user_id == current_user.id)
        .order_by(ProgressLog.logged_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
