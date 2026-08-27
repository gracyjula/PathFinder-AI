"""Pydantic schemas for Learner Profile, Roadmap, Chat."""
import json
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, model_validator


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_json_field(v: Any) -> list | dict:
    """Parse a JSON string or pass through a list/dict."""
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return []
    return v or []


# ─── Learner Profile ──────────────────────────────────────────────────────────

class ProfileCreate(BaseModel):
    education: Optional[str] = None
    degree: Optional[str] = None
    year_of_study: Optional[int] = None
    institution: Optional[str] = None
    career_goal: Optional[str] = None
    learning_goal: Optional[str] = None
    target_timeline_months: Optional[int] = 12
    current_skills: list[str] = []
    completed_courses: list[str] = []
    interests: list[str] = []
    experience_level: str = "beginner"
    learning_style: str = "mixed"
    weekly_hours: Optional[int] = 10
    preferred_difficulty: str = "beginner"
    preferred_languages: list[str] = ["English"]


class ProfileUpdate(ProfileCreate):
    pass


class ProfileOut(BaseModel):
    id: str
    user_id: str
    education: Optional[str] = None
    degree: Optional[str] = None
    year_of_study: Optional[int] = None
    institution: Optional[str] = None
    career_goal: Optional[str] = None
    learning_goal: Optional[str] = None
    target_timeline_months: Optional[int] = None
    current_skills: list[str] = []
    completed_courses: list[str] = []
    interests: list[str] = []
    experience_level: str = "beginner"
    learning_style: str = "mixed"
    weekly_hours: Optional[int] = None
    preferred_difficulty: str = "beginner"
    preferred_languages: list[str] = ["English"]
    career_readiness_score: Optional[float] = 0.0
    skill_gap_report: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_json_strings(cls, values):
        """Convert JSON string fields from SQLite to Python lists/dicts."""
        if hasattr(values, "__dict__"):
            # ORM object
            obj = values
            for field in ["current_skills", "completed_courses", "interests", "preferred_languages"]:
                raw = getattr(obj, field, None)
                if isinstance(raw, str):
                    try:
                        setattr(obj, field, json.loads(raw))
                    except Exception:
                        setattr(obj, field, [])
            raw_gap = getattr(obj, "skill_gap_report", None)
            if isinstance(raw_gap, str):
                try:
                    setattr(obj, "skill_gap_report", json.loads(raw_gap))
                except Exception:
                    setattr(obj, "skill_gap_report", None)
        return values


# ─── Roadmap ──────────────────────────────────────────────────────────────────

class MilestoneOut(BaseModel):
    id: str
    month_number: int
    title: str
    description: Optional[str]
    topics: list[str] = []
    resources: list[dict] = []
    projects: list[dict] = []
    estimated_hours: Optional[int]
    difficulty: str
    is_completed: bool
    completed_at: Optional[datetime]
    outcomes: list[str] = []

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_json_strings(cls, values):
        if hasattr(values, "__dict__"):
            obj = values
            for field in ["topics", "resources", "projects", "outcomes"]:
                raw = getattr(obj, field, None)
                if isinstance(raw, str):
                    try:
                        setattr(obj, field, json.loads(raw))
                    except Exception:
                        setattr(obj, field, [])
        return values


class RoadmapOut(BaseModel):
    id: str
    user_id: str
    title: str
    goal: str
    description: Optional[str]
    status: str
    total_months: int
    completion_percentage: float
    milestones: list[MilestoneOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoadmapCreate(BaseModel):
    goal: str
    target_timeline_months: Optional[int] = 12


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessageIn(BaseModel):
    content: str
    session_id: Optional[str] = None


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_metadata(cls, values):
        if hasattr(values, "__dict__"):
            raw = getattr(values, "metadata_json", None)
            if isinstance(raw, str):
                try:
                    values.__dict__["metadata"] = json.loads(raw)
                except Exception:
                    values.__dict__["metadata"] = None
        return values


class ChatSessionOut(BaseModel):
    id: str
    title: Optional[str]
    session_type: str
    messages: list[ChatMessageOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Skill Gap ────────────────────────────────────────────────────────────────

class SkillGapRequest(BaseModel):
    current_skills: list[str]
    target_role: str


class SkillGapReport(BaseModel):
    target_role: str
    required_skills: list[str]
    current_skills: list[str]
    missing_skills: list[str]
    gap_percentage: float
    skill_scores: dict[str, float]
    recommendations: list[str]


# ─── Progress ─────────────────────────────────────────────────────────────────

class ProgressLogCreate(BaseModel):
    roadmap_id: Optional[str] = None
    milestone_id: Optional[str] = None
    activity_type: str
    resource_title: Optional[str] = None
    notes: Optional[str] = None
    hours_spent: Optional[float] = 0.0


class ProgressLogOut(ProgressLogCreate):
    id: str
    user_id: str
    logged_at: datetime

    model_config = {"from_attributes": True}


# ─── Quiz ─────────────────────────────────────────────────────────────────────

class QuizRequest(BaseModel):
    topic: str
    difficulty: str = "intermediate"
    num_questions: int = 5


class QuizSubmit(BaseModel):
    topic: str
    answers: dict[str, Any]
    questions: dict[str, Any]


# ─── Resume ───────────────────────────────────────────────────────────────────

class ResumeAnalysisResult(BaseModel):
    extracted_skills: list[str]
    experience_level: str
    education: Optional[str]
    target_role_match: Optional[dict]


# ─── Career Readiness ─────────────────────────────────────────────────────────

class CareerReadinessOut(BaseModel):
    score: float
    breakdown: dict[str, float]
    weak_areas: list[str]
    strong_areas: list[str]
    suggestions: list[str]


# ─── Weekly Plan ──────────────────────────────────────────────────────────────

class WeeklyPlanOut(BaseModel):
    week_number: int
    goal: str
    daily_plans: list[dict]
    total_hours: float
    focus_topics: list[str]
