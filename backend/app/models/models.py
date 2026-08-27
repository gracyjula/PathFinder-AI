"""
NeuraLearn AI - Database Models
SQLAlchemy ORM models compatible with both SQLite (dev) and PostgreSQL (prod).
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, JSON,
    ForeignKey, Enum as SAEnum, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.session import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class LearningStyle(str, enum.Enum):
    VISUAL = "visual"
    READING = "reading"
    HANDS_ON = "hands_on"
    MIXED = "mixed"


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class RoadmapStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class ResourceType(str, enum.Enum):
    COURSE = "course"
    VIDEO = "video"
    ARTICLE = "article"
    PROJECT = "project"
    CERTIFICATION = "certification"
    BOOK = "book"
    RESEARCH_PAPER = "research_paper"
    COMMUNITY = "community"
    PRACTICE_PLATFORM = "practice_platform"


def new_uuid() -> str:
    return str(uuid.uuid4())


# ─── User & Auth ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile: Mapped[Optional["LearnerProfile"]] = relationship("LearnerProfile", back_populates="user", uselist=False)
    roadmaps: Mapped[list["Roadmap"]] = relationship("Roadmap", back_populates="user")
    chat_sessions: Mapped[list["ChatSession"]] = relationship("ChatSession", back_populates="user")
    progress_logs: Mapped[list["ProgressLog"]] = relationship("ProgressLog", back_populates="user")
    quiz_results: Mapped[list["QuizResult"]] = relationship("QuizResult", back_populates="user")
    streak: Mapped[Optional["LearningStreak"]] = relationship("LearningStreak", back_populates="user", uselist=False)
    skill_masteries: Mapped[list["SkillMastery"]] = relationship("SkillMastery", back_populates="user")


# ─── Learner Profile ──────────────────────────────────────────────────────────

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True)

    education: Mapped[Optional[str]] = mapped_column(String(200))
    degree: Mapped[Optional[str]] = mapped_column(String(100))
    year_of_study: Mapped[Optional[int]] = mapped_column(Integer)
    institution: Mapped[Optional[str]] = mapped_column(String(200))

    career_goal: Mapped[Optional[str]] = mapped_column(String(300))
    learning_goal: Mapped[Optional[str]] = mapped_column(Text)
    target_timeline_months: Mapped[Optional[int]] = mapped_column(Integer)

    current_skills: Mapped[str] = mapped_column(Text, default="[]")       # JSON string
    completed_courses: Mapped[str] = mapped_column(Text, default="[]")
    interests: Mapped[str] = mapped_column(Text, default="[]")
    experience_level: Mapped[str] = mapped_column(String(50), default="beginner")

    learning_style: Mapped[str] = mapped_column(String(20), default="mixed")
    weekly_hours: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    preferred_difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    preferred_languages: Mapped[str] = mapped_column(Text, default='["English"]')

    career_readiness_score: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    skill_gap_report: Mapped[Optional[str]] = mapped_column(Text)          # JSON string
    resume_text: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")


# ─── Roadmap & Milestones ─────────────────────────────────────────────────────

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300))
    goal: Mapped[str] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    total_months: Mapped[int] = mapped_column(Integer, default=12)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    ai_generated_data: Mapped[Optional[str]] = mapped_column(Text)         # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="roadmaps")
    milestones: Mapped[list["Milestone"]] = relationship(
        "Milestone", back_populates="roadmap", cascade="all, delete-orphan", order_by="Milestone.month_number"
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    roadmap_id: Mapped[str] = mapped_column(String(36), ForeignKey("roadmaps.id", ondelete="CASCADE"))
    month_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[Optional[str]] = mapped_column(Text)
    topics: Mapped[str] = mapped_column(Text, default="[]")                # JSON string
    resources: Mapped[str] = mapped_column(Text, default="[]")
    projects: Mapped[str] = mapped_column(Text, default="[]")
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    outcomes: Mapped[str] = mapped_column(Text, default="[]")

    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="milestones")


# ─── Resources ────────────────────────────────────────────────────────────────

class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    resource_type: Mapped[str] = mapped_column(String(50))
    provider: Mapped[Optional[str]] = mapped_column(String(200))
    skills_covered: Mapped[str] = mapped_column(Text, default="[]")
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    duration_hours: Mapped[Optional[float]] = mapped_column(Float)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    tags: Mapped[str] = mapped_column(Text, default="[]")
    embedding_id: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ─── Chat Sessions ────────────────────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(300))
    session_type: Mapped[str] = mapped_column(String(50), default="onboarding")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)             # JSON string (renamed to avoid clash)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")


# ─── Progress & Assessments ───────────────────────────────────────────────────

class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    roadmap_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("roadmaps.id", ondelete="SET NULL"))
    milestone_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("milestones.id", ondelete="SET NULL"))
    activity_type: Mapped[str] = mapped_column(String(100))
    resource_title: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    hours_spent: Mapped[Optional[float]] = mapped_column(Float, default=0.0)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="progress_logs")


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    topic: Mapped[str] = mapped_column(String(200))
    score: Mapped[float] = mapped_column(Float)
    max_score: Mapped[float] = mapped_column(Float, default=100.0)
    questions_json: Mapped[Optional[str]] = mapped_column(Text)            # JSON string
    feedback: Mapped[Optional[str]] = mapped_column(Text)
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="quiz_results")


# ─── Streak Tracking ──────────────────────────────────────────────────────────

class LearningStreak(Base):
    __tablename__ = "learning_streaks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    total_days_active: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped["User"] = relationship("User", back_populates="streak")


# ─── Skill Mastery ────────────────────────────────────────────────────────────

class SkillMastery(Base):
    """
    Per-user, per-skill mastery score (0–100).
    Updated deterministically from quiz results and onboarding self-assessment.
    Never written by the LLM directly.
    """
    __tablename__ = "skill_mastery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)          # 0–100
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)           # how many data points
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="skill_masteries")


# ─── Adaptation Events ────────────────────────────────────────────────────────

class AdaptationEvent(Base):
    """
    Records every time the system adapted a roadmap based on mastery evidence.
    Provides an audit trail and powers the UI "roadmap was adapted" notice.
    """
    __tablename__ = "adaptation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    roadmap_id: Mapped[str] = mapped_column(String(36), ForeignKey("roadmaps.id", ondelete="CASCADE"))
    trigger: Mapped[str] = mapped_column(String(100))           # "quiz_result" | "milestone_complete" | "manual"
    skill: Mapped[Optional[str]] = mapped_column(String(200))
    old_mastery: Mapped[Optional[float]] = mapped_column(Float)
    new_mastery: Mapped[Optional[float]] = mapped_column(Float)
    action_taken: Mapped[str] = mapped_column(Text)             # human-readable description
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


# ─── Industry Trends ──────────────────────────────────────────────────────────

class IndustryTrend(Base):
    __tablename__ = "industry_trends"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    skill_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    demand_score: Mapped[float] = mapped_column(Float, default=0.0)
    job_count: Mapped[Optional[int]] = mapped_column(Integer)
    growth_rate: Mapped[Optional[float]] = mapped_column(Float)
    related_roles: Mapped[str] = mapped_column(Text, default="[]")
    sources: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
