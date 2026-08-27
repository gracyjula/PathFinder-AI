"""Admin dashboard routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc

from app.db.session import get_db
from app.models.models import User, LearnerProfile, Roadmap, QuizResult
from app.core.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total_users = await db.execute(select(sqlfunc.count(User.id)))
    active_users = await db.execute(select(sqlfunc.count(User.id)).where(User.is_active == True))
    total_roadmaps = await db.execute(select(sqlfunc.count(Roadmap.id)))
    avg_readiness = await db.execute(select(sqlfunc.avg(LearnerProfile.career_readiness_score)))
    quiz_avg = await db.execute(select(sqlfunc.avg(QuizResult.score)))

    # Most common goals
    goals = await db.execute(
        select(LearnerProfile.career_goal, sqlfunc.count(LearnerProfile.id).label("count"))
        .where(LearnerProfile.career_goal.isnot(None))
        .group_by(LearnerProfile.career_goal)
        .order_by(sqlfunc.count(LearnerProfile.id).desc())
        .limit(10)
    )

    return {
        "total_users": total_users.scalar() or 0,
        "active_users": active_users.scalar() or 0,
        "total_roadmaps": total_roadmaps.scalar() or 0,
        "avg_career_readiness": round(avg_readiness.scalar() or 0, 1),
        "avg_quiz_score": round(quiz_avg.scalar() or 0, 1),
        "popular_goals": [{"goal": r[0], "count": r[1]} for r in goals.all()],
    }


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]
