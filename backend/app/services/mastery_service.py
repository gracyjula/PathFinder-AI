"""
NeuraLearn AI — Mastery Service
================================
All read/write operations for skill mastery scores.
Keeps the deterministic math in skill_graph.py and the DB logic here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import SkillMastery, LearnerProfile, AdaptationEvent
from app.services.skill_graph import (
    normalize_skill,
    build_mastery_map_from_skills,
    update_mastery_from_quiz,
    calculate_skill_gap,
    get_next_best_actions,
    SkillGapResult,
)


# ─── Read helpers ─────────────────────────────────────────────────────────────

async def get_mastery_map(db: AsyncSession, user_id: str) -> dict[str, float]:
    """Return {skill: mastery_score} for a user. Canonical names."""
    result = await db.execute(
        select(SkillMastery).where(SkillMastery.user_id == user_id)
    )
    rows = result.scalars().all()
    return {row.skill: row.mastery_score for row in rows}


async def get_mastery_rows(db: AsyncSession, user_id: str) -> list[SkillMastery]:
    result = await db.execute(
        select(SkillMastery).where(SkillMastery.user_id == user_id)
    )
    return result.scalars().all()


# ─── Write helpers ────────────────────────────────────────────────────────────

async def upsert_mastery(
    db: AsyncSession,
    user_id: str,
    skill: str,
    new_score: float,
    flush: bool = True,
) -> SkillMastery:
    """Insert or update a mastery row. Returns the updated row."""
    result = await db.execute(
        select(SkillMastery).where(
            SkillMastery.user_id == user_id,
            SkillMastery.skill == skill,
        )
    )
    row = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if row:
        row.mastery_score = new_score
        row.evidence_count += 1
        row.last_assessed_at = now
        row.updated_at = now
    else:
        row = SkillMastery(
            user_id=user_id,
            skill=skill,
            mastery_score=new_score,
            evidence_count=1,
            last_assessed_at=now,
        )
        db.add(row)

    if flush:
        await db.flush()
    return row


# ─── Initialize from onboarding ───────────────────────────────────────────────

async def initialize_mastery_from_profile(
    db: AsyncSession,
    user_id: str,
    profile: LearnerProfile,
) -> dict[str, float]:
    """
    Called once after onboarding completes.
    Seeds SkillMastery rows from the flat skill list the learner provided.
    Only creates rows that don't already exist.
    """
    raw = profile.current_skills
    known_skills: list[str] = json.loads(raw) if isinstance(raw, str) else (raw or [])

    mastery_map = build_mastery_map_from_skills(
        known_skills, profile.experience_level or "beginner"
    )

    existing = await get_mastery_map(db, user_id)

    for skill, score in mastery_map.items():
        if skill not in existing:
            await upsert_mastery(db, user_id, skill, score, flush=False)

    await db.flush()
    return {**existing, **{k: v for k, v in mastery_map.items() if k not in existing}}


# ─── Update mastery after a quiz ─────────────────────────────────────────────

async def apply_quiz_result(
    db: AsyncSession,
    user_id: str,
    topic: str,
    quiz_score: float,          # 0–100
) -> tuple[float, float]:
    """
    Apply a quiz result to the relevant skill's mastery score.
    Returns (old_mastery, new_mastery).
    """
    canonical = normalize_skill(topic)

    result = await db.execute(
        select(SkillMastery).where(
            SkillMastery.user_id == user_id,
            SkillMastery.skill == canonical,
        )
    )
    row = result.scalar_one_or_none()
    old_mastery = row.mastery_score if row else 0.0
    evidence_count = row.evidence_count if row else 0

    new_mastery = update_mastery_from_quiz(old_mastery, quiz_score, evidence_count)
    await upsert_mastery(db, user_id, canonical, new_mastery)
    return old_mastery, new_mastery


# ─── Full skill-gap report from mastery data ─────────────────────────────────

async def get_skill_gap_for_user(
    db: AsyncSession,
    user_id: str,
    target_role: str,
    experience_level: str = "beginner",
) -> SkillGapResult:
    """
    Compute the skill-gap report for a user against a target role.
    Uses real mastery scores from the DB — no AI involved.
    """
    mastery_map = await get_mastery_map(db, user_id)
    return calculate_skill_gap(target_role, mastery_map, experience_level)


# ─── Next Best Action ─────────────────────────────────────────────────────────

async def get_next_best_action(
    db: AsyncSession,
    user_id: str,
    target_role: str,
    weekly_hours: int = 10,
) -> list[dict]:
    """Return the top 3 learning actions based on current mastery gaps."""
    mastery_map = await get_mastery_map(db, user_id)
    gap_result = calculate_skill_gap(target_role, mastery_map)
    return get_next_best_actions(gap_result, mastery_map, weekly_hours)


# ─── Record adaptation event ──────────────────────────────────────────────────

async def record_adaptation(
    db: AsyncSession,
    user_id: str,
    roadmap_id: str,
    trigger: str,
    skill: Optional[str],
    old_mastery: Optional[float],
    new_mastery: Optional[float],
    action_taken: str,
) -> AdaptationEvent:
    event = AdaptationEvent(
        user_id=user_id,
        roadmap_id=roadmap_id,
        trigger=trigger,
        skill=skill,
        old_mastery=old_mastery,
        new_mastery=new_mastery,
        action_taken=action_taken,
    )
    db.add(event)
    await db.flush()
    return event
