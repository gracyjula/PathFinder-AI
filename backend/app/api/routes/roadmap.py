"""Roadmap routes - CRUD + milestone management + adaptive updates."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import User, Roadmap, Milestone, LearnerProfile
from app.schemas.schemas import RoadmapOut, RoadmapCreate
from app.core.deps import get_current_user
from app.ai.ai_service import generate_roadmap
from app.services.roadmap_service import create_roadmap_from_ai, recalculate_roadmap_progress

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])


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
        "current_skills": profile.current_skills if profile else [],
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
    from datetime import datetime, timezone

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
