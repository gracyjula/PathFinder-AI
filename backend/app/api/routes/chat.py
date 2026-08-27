"""Chat routes - Conversational AI with session management."""
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
    """
    Send a message to the AI mentor. Creates a new session if session_id is None.
    Returns AI response with optional roadmap generation.
    """
    # Get or create session
    if payload.session_id:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id)
            .options(selectinload(ChatSession.messages))
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = ChatSession(user_id=current_user.id, session_type="onboarding", title="New Conversation")
        db.add(session)
        await db.flush()
        session.messages = []

    # Build history for AI
    history = [{"role": m.role, "content": m.content} for m in session.messages[-10:]]

    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=payload.content)
    db.add(user_msg)
    await db.flush()

    # Get learner profile for context
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    profile_dict = None
    if profile:
        profile_dict = {
            "career_goal": profile.career_goal,
            "current_skills": profile.current_skills,
            "experience_level": profile.experience_level,
            "weekly_hours": profile.weekly_hours,
            "learning_style": profile.learning_style,
        }

    # Get active roadmap context
    roadmap_result = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == current_user.id, Roadmap.status == "active")
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    roadmap = roadmap_result.scalar_one_or_none()
    roadmap_ctx = None
    if roadmap:
        roadmap_ctx = {"title": roadmap.title, "completion_percentage": roadmap.completion_percentage}

    # Analyze intent
    intent_data = await analyze_learner_intent(payload.content, history)

    generated_roadmap = None
    ai_response_text = ""

    if intent_data.get("has_enough_for_roadmap") and not roadmap:
        # Generate roadmap from conversation
        merged_profile = {
            "career_goal": intent_data.get("extracted_goal") or (profile.career_goal if profile else ""),
            "current_skills": intent_data.get("current_skills") or (profile.current_skills if profile else []),
            "experience_level": intent_data.get("experience_level", "beginner"),
            "target_timeline_months": intent_data.get("timeline_months", 12),
            "weekly_hours": profile.weekly_hours if profile else 10,
            "learning_style": profile.learning_style if profile else "mixed",
            "education": intent_data.get("education") or (profile.education if profile else ""),
        }
        roadmap_data = await generate_roadmap(merged_profile)
        generated_roadmap = await create_roadmap_from_ai(db, current_user.id, roadmap_data)

        ai_response_text = f"""🎉 **Your personalized roadmap is ready!**

I've analyzed your background and created a **{roadmap_data.get('total_months', 12)}-month roadmap** to help you become a **{merged_profile['career_goal']}**.

**📍 Your roadmap includes:**
- {len(roadmap_data.get('milestones', []))} monthly milestones
- Curated resources for each stage
- Hands-on projects at every level

**🚀 Month 1 starts with:** {roadmap_data['milestones'][0]['title'] if roadmap_data.get('milestones') else 'Foundation topics'}

You can view your complete roadmap in the **Roadmap** section. Let me know if you have questions about any step!"""
    else:
        # Regular mentor response
        if intent_data.get("follow_up_question") and intent_data.get("intent") == "onboarding":
            ai_response_text = intent_data["follow_up_question"]
        else:
            ai_response_text = await generate_mentor_response(
                payload.content, history, profile_dict, roadmap_ctx
            )

    # Update session title from first message
    if not session.title or session.title == "New Conversation":
        session.title = payload.content[:60] + ("..." if len(payload.content) > 60 else "")

    # Save AI response
    ai_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response_text,
        metadata={"roadmap_generated": bool(generated_roadmap), "intent": intent_data.get("intent")},
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
            "metadata": ai_msg.metadata,
            "created_at": ai_msg.created_at,
        },
        "roadmap_generated": bool(generated_roadmap),
        "roadmap_id": str(generated_roadmap.id) if generated_roadmap else None,
    }
