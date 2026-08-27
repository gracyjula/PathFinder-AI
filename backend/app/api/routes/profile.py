"""Learner profile routes."""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import User, LearnerProfile
from app.schemas.schemas import ProfileCreate, ProfileOut, ProfileUpdate
from app.core.deps import get_current_user
from app.services.mastery_service import initialize_mastery_from_profile

router = APIRouter(prefix="/profile", tags=["Learner Profile"])

# Fields stored as JSON strings in the DB
_JSON_LIST_FIELDS = {"current_skills", "completed_courses", "interests", "preferred_languages"}


def _serialize_profile_payload(data: dict) -> dict:
    """Convert list fields to JSON strings for storage."""
    out = {}
    for k, v in data.items():
        if k in _JSON_LIST_FIELDS and isinstance(v, list):
            out[k] = json.dumps(v)
        else:
            out[k] = v
    return out


@router.post("", response_model=ProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: ProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if profile already exists
    result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Profile already exists. Use PATCH to update.")

    profile = LearnerProfile(user_id=current_user.id, **_serialize_profile_payload(payload.model_dump()))
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    # Seed skill mastery from onboarding profile (runs deterministically, no AI)
    await initialize_mastery_from_profile(db, current_user.id, profile)
    await db.commit()

    return profile


@router.get("", response_model=ProfileOut)
async def get_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Please complete onboarding.")
    return profile


@router.patch("", response_model=ProfileOut)
async def update_profile(
    payload: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(LearnerProfile).where(LearnerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    for field, value in _serialize_profile_payload(payload.model_dump(exclude_none=True)).items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    # Re-seed mastery for any new skills that appeared
    await initialize_mastery_from_profile(db, current_user.id, profile)
    await db.commit()

    return profile
