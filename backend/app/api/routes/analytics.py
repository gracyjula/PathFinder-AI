"""Analytics, Quiz, Resume, and Career Readiness routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc

from app.db.session import get_db
from app.models.models import User, LearnerProfile, QuizResult, ProgressLog, Roadmap, Milestone, LearningStreak
from app.schemas.schemas import (
    SkillGapRequest, SkillGapReport, ProgressLogCreate, ProgressLogOut,
    QuizRequest, QuizSubmit, CareerReadinessOut, WeeklyPlanOut, ResumeAnalysisResult
)
from app.core.deps import get_current_user
from app.ai.ai_service import (
    analyze_skill_gap, calculate_career_readiness, generate_quiz,
    generate_weekly_plan, analyze_resume, generate_mock_interview_questions
)

router = APIRouter(prefix="/analytics", tags=["Analytics & AI Tools"])


# ─── Skill Gap ────────────────────────────────────────────────────────────────

@router.post("/skill-gap", response_model=dict)
async def skill_gap_analysis(
    payload: SkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await analyze_skill_gap(payload.current_skills, payload.target_role)

    # Persist to profile
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.skill_gap_report = result
        await db.commit()

    return result


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
            sqlfunc.sum(Milestone.is_completed.cast("int")).label("completed"),
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
        "current_skills": profile.current_skills,
        "completed_courses": profile.completed_courses,
        "experience_level": profile.experience_level,
    }

    result = await calculate_career_readiness(profile_dict, progress_data)

    # Update score in profile
    profile.career_readiness_score = result.get("score", 0)
    await db.commit()

    return result


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

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
            sqlfunc.sum(Milestone.is_completed.cast("int")).label("completed"),
        )
        .join(Roadmap)
        .where(Roadmap.user_id == current_user.id)
    )
    m_stats = milestone_stats.one()

    return {
        "profile": {
            "career_goal": profile.career_goal if profile else None,
            "career_readiness_score": profile.career_readiness_score if profile else 0,
            "current_skills": profile.current_skills if profile else [],
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
    """Evaluate quiz answers and save result."""
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

    quiz_result = QuizResult(
        user_id=current_user.id,
        topic=payload.topic,
        score=round(score, 1),
        questions=payload.questions,
        feedback="\n".join(feedback_items) if feedback_items else "All correct!",
    )
    db.add(quiz_result)
    await db.commit()

    return {
        "score": round(score, 1),
        "correct": correct,
        "total": len(questions),
        "feedback": feedback_items,
        "passed": score >= 60,
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
        "current_skills": profile.current_skills,
    }

    return await generate_weekly_plan(profile_dict, milestone_dict)


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
        existing = set(profile.current_skills)
        new_skills = list(existing | set(result.get("extracted_skills", [])))
        profile.current_skills = new_skills
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
    skills = profile.current_skills if profile else []
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
