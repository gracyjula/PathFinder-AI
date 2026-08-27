"""Roadmap routes - CRUD + milestone management + adaptive updates."""
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import User, Roadmap, Milestone, LearnerProfile
from app.schemas.schemas import RoadmapOut, RoadmapCreate
from app.core.deps import get_current_user
from app.ai.ai_service import generate_roadmap, generate_adaptation_explanation
from app.services.roadmap_service import create_roadmap_from_ai, recalculate_roadmap_progress
from app.services.mastery_service import get_mastery_map, record_adaptation
from app.services.skill_graph import calculate_skill_gap, STRONG_THRESHOLD, DEVELOPING_THRESHOLD

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


def _parse_skills(raw) -> list:
    """Safely parse skills whether stored as JSON string or already a list."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return []
    return []


@router.get("", response_model=list[RoadmapOut])
async def list_roadmaps(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.user_id == current_user.id)
        .options(selectinload(Roadmap.milestones))
        .order_by(Roadmap.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{roadmap_id}", response_model=RoadmapOut)
async def get_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.id == roadmap_id, Roadmap.user_id == current_user.id)
        .options(selectinload(Roadmap.milestones))
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return roadmap


@router.post("", response_model=RoadmapOut, status_code=201)
async def generate_new_roadmap(
    payload: RoadmapCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a new AI roadmap from a goal description."""
    # Load profile for context
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    profile_data = {
        "career_goal": payload.goal,
        "current_skills": _parse_skills(profile.current_skills) if profile else [],
        "experience_level": profile.experience_level if profile else "beginner",
        "target_timeline_months": payload.target_timeline_months or 12,
        "weekly_hours": profile.weekly_hours if profile else 10,
        "learning_style": profile.learning_style if profile else "mixed",
        "education": profile.education if profile else "",
    }

    roadmap_data = await generate_roadmap(profile_data)
    roadmap = await create_roadmap_from_ai(db, current_user.id, roadmap_data)
    await db.commit()
    await db.refresh(roadmap)

    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.id == roadmap.id)
        .options(selectinload(Roadmap.milestones))
    )
    return result.scalar_one()


@router.patch("/{roadmap_id}/milestone/{milestone_id}/complete", response_model=dict)
async def complete_milestone(
    roadmap_id: uuid.UUID,
    milestone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a milestone as completed and recalculate progress."""
    result = await db.execute(
        select(Milestone)
        .join(Roadmap)
        .where(
            Milestone.id == milestone_id,
            Roadmap.id == roadmap_id,
            Roadmap.user_id == current_user.id,
        )
    )
    milestone = result.scalar_one_or_none()
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    milestone.is_completed = True
    milestone.completed_at = datetime.now(timezone.utc)
    await db.flush()

    pct = await recalculate_roadmap_progress(db, roadmap_id)
    await db.commit()
    return {"message": "Milestone completed", "completion_percentage": pct}


@router.post("/{roadmap_id}/adapt", response_model=dict)
async def adapt_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Adapt the roadmap based on current skill mastery.
    This is the adaptive learning engine — it:
    1. Reads current mastery from SkillMastery table (deterministic)
    2. Recalculates which milestones are now acceleratable or need reinforcement
    3. Updates milestone difficulty and inserts/removes focus notes
    4. Records an AdaptationEvent

    It does NOT reorder milestones (that would break user context).
    Instead it annotates each milestone with an adaptation status.
    """
    result = await db.execute(
        select(Roadmap)
        .where(Roadmap.id == roadmap_id, Roadmap.user_id == current_user.id)
        .options(selectinload(Roadmap.milestones))
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    # Get learner profile for target role
    profile_result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    target_role = (profile.career_goal if profile else None) or roadmap.goal

    # Get current mastery
    mastery_map = await get_mastery_map(db, current_user.id)
    gap_result = calculate_skill_gap(target_role, mastery_map)

    # Build skill → status lookup
    skill_status = {item.skill: item for item in gap_result.required_skills}

    adaptations = []
    for milestone in roadmap.milestones:
        if milestone.is_completed:
            continue

        topics_raw = milestone.topics
        topics: list[str] = json.loads(topics_raw) if isinstance(topics_raw, str) else (topics_raw or [])

        milestone_adaptations = []
        can_accelerate = True
        needs_reinforcement = False

        for topic in topics:
            item = skill_status.get(topic)
            if item is None:
                # Normalize and try again
                from app.services.skill_graph import normalize_skill
                canonical = normalize_skill(topic)
                item = skill_status.get(canonical)

            if item:
                if item.status == "strong":
                    milestone_adaptations.append({
                        "skill": topic,
                        "action": "accelerate",
                        "reason": f"Already strong at {item.current_mastery:.0f}% — can skim or skip basics",
                    })
                elif item.status == "gap":
                    can_accelerate = False
                    needs_reinforcement = True
                    milestone_adaptations.append({
                        "skill": topic,
                        "action": "reinforce",
                        "reason": f"Gap detected at {item.current_mastery:.0f}% mastery — needs focused study",
                    })
                else:
                    can_accelerate = False
                    milestone_adaptations.append({
                        "skill": topic,
                        "action": "normal",
                        "reason": f"Developing at {item.current_mastery:.0f}% — follow planned resources",
                    })

        if milestone_adaptations:
            adaptation_status = "accelerate" if can_accelerate else ("reinforce" if needs_reinforcement else "normal")
            adaptations.append({
                "milestone_id": milestone.id,
                "milestone_title": milestone.title,
                "month_number": milestone.month_number,
                "adaptation_status": adaptation_status,
                "skill_adaptations": milestone_adaptations,
            })

    # Store adaptation summary on roadmap
    adaptation_summary = {
        "adapted_at": datetime.now(timezone.utc).isoformat(),
        "target_role": target_role,
        "career_readiness_pct": gap_result.career_readiness_pct,
        "adaptations": adaptations,
    }

    # Store in ai_generated_data as adaptation metadata
    existing_data = {}
    if roadmap.ai_generated_data:
        try:
            existing_data = json.loads(roadmap.ai_generated_data)
        except Exception:
            pass
    existing_data["last_adaptation"] = adaptation_summary
    roadmap.ai_generated_data = json.dumps(existing_data)

    # Record the adaptation event
    if adaptations:
        summary_text = (
            f"Adapted {len(adaptations)} milestones: "
            f"{sum(1 for a in adaptations if a['adaptation_status'] == 'accelerate')} to accelerate, "
            f"{sum(1 for a in adaptations if a['adaptation_status'] == 'reinforce')} needing reinforcement"
        )
        await record_adaptation(
            db=db,
            user_id=current_user.id,
            roadmap_id=str(roadmap_id),
            trigger="manual_adapt",
            skill=None,
            old_mastery=None,
            new_mastery=None,
            action_taken=summary_text,
        )

    await db.commit()

    return {
        "roadmap_id": str(roadmap_id),
        "career_readiness_pct": gap_result.career_readiness_pct,
        "adaptations": adaptations,
        "summary": f"Roadmap adapted: {len(adaptations)} milestones reviewed based on current mastery",
    }


@router.get("/{roadmap_id}/adaptation-history", response_model=list[dict])
async def get_adaptation_history(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the adaptation event history for a roadmap."""
    from app.models.models import AdaptationEvent
    result = await db.execute(
        select(AdaptationEvent)
        .where(
            AdaptationEvent.roadmap_id == roadmap_id,
            AdaptationEvent.user_id == current_user.id,
        )
        .order_by(AdaptationEvent.created_at.desc())
        .limit(20)
    )
    events = result.scalars().all()
    return [
        {
            "id": e.id,
            "trigger": e.trigger,
            "skill": e.skill,
            "old_mastery": e.old_mastery,
            "new_mastery": e.new_mastery,
            "action_taken": e.action_taken,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.delete("/{roadmap_id}", status_code=204)
async def delete_roadmap(
    roadmap_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Roadmap).where(Roadmap.id == roadmap_id, Roadmap.user_id == current_user.id)
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    await db.delete(roadmap)
    await db.commit()
