"""Chat routes - Conversational AI with session management."""
import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import User, ChatSession, ChatMessage, LearnerProfile, Roadmap
from app.schemas.schemas import ChatMessageIn, ChatMessageOut, ChatSessionOut
from app.core.deps import get_current_user
from app.ai.ai_service import analyze_learner_intent, generate_mentor_response, generate_roadmap
from app.services.roadmap_service import create_roadmap_from_ai

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat & AI Mentor"])


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
        .order_by(ChatSession.updated_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.post("/sessions", response_model=ChatSessionOut, status_code=201)
async def create_session(
    session_type: str = "mentor",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = ChatSession(user_id=current_user.id, session_type=session_type)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/message", response_model=dict)
async def send_message(
    payload: ChatMessageIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a message to the AI mentor. Generates roadmap when enough info is provided."""
    # ── Session resolution ────────────────────────────────────────────────────
    if payload.session_id:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id)
            .options(selectinload(ChatSession.messages))
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        loaded_messages = list(session.messages)
    else:
        session = ChatSession(user_id=current_user.id, session_type="mentor", title="New Conversation")
        db.add(session)
        await db.flush()
        loaded_messages = []  # new session — no prior messages, avoids lazy-load

    # Build history from the already-loaded list
    history = [{"role": m.role, "content": m.content} for m in loaded_messages[-10:]]

    # Save user message first
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.content)
    db.add(user_msg)
    await db.flush()

    # ── Load learner profile ──────────────────────────────────────────────────
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_dict = None
    if profile:
        raw_skills = profile.current_skills
        parsed_skills = json.loads(raw_skills) if isinstance(raw_skills, str) else (raw_skills or [])
        profile_dict = {
            "career_goal": profile.career_goal,
            "current_skills": parsed_skills,
            "experience_level": profile.experience_level,
            "weekly_hours": profile.weekly_hours,
            "learning_style": profile.learning_style,
        }

    # ── Load mastery context for grounded answers ─────────────────────────────
    from app.services.mastery_service import get_mastery_map as _get_mastery
    mastery_map = await _get_mastery(db, current_user.id)

    # ── Check for existing roadmaps (any status, not just active) ────────────
    # We allow regeneration if user explicitly asks for a new roadmap
    roadmap_result = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == current_user.id, Roadmap.status == "active")
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    existing_roadmap = roadmap_result.scalar_one_or_none()
    roadmap_ctx = None
    if existing_roadmap:
        roadmap_ctx = {"title": existing_roadmap.title, "completion_percentage": existing_roadmap.completion_percentage}

    # ── Analyze intent ────────────────────────────────────────────────────────
    intent_data = await analyze_learner_intent(payload.content, history)

    generated_roadmap = None
    ai_response_text = ""

    # Detect explicit roadmap regeneration request
    regen_keywords = ["new roadmap", "regenerate", "create roadmap", "generate roadmap", "make a roadmap", "build a roadmap"]
    wants_new_roadmap = any(kw in payload.content.lower() for kw in regen_keywords)

    should_generate = (
        intent_data.get("has_enough_for_roadmap")
        and (not existing_roadmap or wants_new_roadmap)
    )

    if should_generate:
        try:
            merged_profile = {
                "career_goal": (
                    intent_data.get("extracted_goal")
                    or (profile.career_goal if profile else "")
                    or payload.content[:80]
                ),
                "current_skills": (
                    intent_data.get("current_skills")
                    or (json.loads(profile.current_skills) if profile and isinstance(profile.current_skills, str) else [])
                    or []
                ),
                "experience_level": intent_data.get("experience_level") or (profile.experience_level if profile else "beginner"),
                "target_timeline_months": intent_data.get("timeline_months") or (profile.target_timeline_months if profile else 12) or 12,
                "weekly_hours": (profile.weekly_hours if profile else 10) or 10,
                "learning_style": (profile.learning_style if profile else "mixed") or "mixed",
                "education": intent_data.get("education") or (profile.education if profile else "") or "",
            }

            # If regenerating, mark old roadmap as paused
            if existing_roadmap and wants_new_roadmap:
                existing_roadmap.status = "paused"
                await db.flush()

            roadmap_data = await generate_roadmap(merged_profile)
            generated_roadmap = await create_roadmap_from_ai(db, current_user.id, roadmap_data)

            milestone_count = len(roadmap_data.get("milestones", []))
            first_title = roadmap_data["milestones"][0]["title"] if roadmap_data.get("milestones") else "Foundation topics"
            ai_response_text = (
                f"🎉 **Your personalized roadmap is ready!**\n\n"
                f"I've created a **{roadmap_data.get('total_months', 12)}-month roadmap** to help you become a **{merged_profile['career_goal']}**.\n\n"
                f"**📍 Your roadmap includes:**\n"
                f"- {milestone_count} monthly milestones with curated resources\n"
                f"- Hands-on projects at every stage\n"
                f"- Progressive difficulty from foundations to advanced\n\n"
                f"**🚀 Month 1 starts with:** {first_title}\n\n"
                f"Head to the **Roadmap** tab to see the full plan. Ask me anything about it!"
            )
        except Exception as e:
            logger.error(f"Roadmap generation failed: {e}")
            ai_response_text = (
                "I have enough information to build your roadmap! "
                "I ran into a small issue generating it right now — you can also create it directly "
                "from the **Roadmap** page. Just paste your goal there and I'll generate it instantly."
            )
    else:
        # Regular mentor response
        if intent_data.get("follow_up_question") and intent_data.get("intent") == "onboarding":
            ai_response_text = intent_data["follow_up_question"]
        else:
            ai_response_text = await generate_mentor_response(
                payload.content, history, profile_dict, roadmap_ctx, mastery_map or None
            )

    # Update session title on first real message
    if not session.title or session.title == "New Conversation":
        session.title = payload.content[:60] + ("..." if len(payload.content) > 60 else "")

    # Save AI response
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response_text,
        metadata_json=json.dumps({
            "roadmap_generated": bool(generated_roadmap),
            "intent": intent_data.get("intent"),
        }),
    )
    db.add(ai_msg)
    await db.commit()
    await db.refresh(ai_msg)

    return {
        "session_id": str(session.id),
        "message": {
            "id": str(ai_msg.id),
            "role": "assistant",
            "content": ai_response_text,
            "metadata": json.loads(ai_msg.metadata_json) if ai_msg.metadata_json else {},
            "created_at": ai_msg.created_at.isoformat(),
        },
        "roadmap_generated": bool(generated_roadmap),
        "roadmap_id": str(generated_roadmap.id) if generated_roadmap else None,
    }
