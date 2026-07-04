from __future__ import annotations
from pydantic import BaseModel, EmailStr, Field


# ── Auth ─────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = ""
    companies: list[str] = Field(default_factory=list)
    weak_areas: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str


# ── User / Profile ──────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    companies: list[str]
    weak_areas: list[str]
    created_at: str


class ProfileResponse(BaseModel):
    user: UserOut
    feedback_summary: list[dict]
    mock_interview_history: list[dict]


# ── Ingest ───────────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    name: str
    role: str = ""
    companies: list[str] = Field(default_factory=list)
    weak_areas: list[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    message: str
    datasets_created: list[str]


# ── Ask ──────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


# ── Feedback ─────────────────────────────────────────────────────────────────

class FeedbackCreateRequest(BaseModel):
    company: str
    topic: str
    result: str
    notes: str = ""


class FeedbackOut(BaseModel):
    id: str
    user_id: str
    company: str
    topic: str
    result: str
    notes: str
    created_at: str


# ── Mock Interview ───────────────────────────────────────────────────────────

class MockInterviewStartRequest(BaseModel):
    company: str
    num_questions: int = 5


class MockInterviewStartResponse(BaseModel):
    interview_id: str
    company: str
    role: str
    questions: list[str]


class MockInterviewEvaluateRequest(BaseModel):
    interview_id: str
    question_number: int
    question: str
    answer: str


class MockInterviewEvaluateResponse(BaseModel):
    interview_id: str
    question_number: int
    score: float
    feedback: str


class MockInterviewHistoryItem(BaseModel):
    id: str
    company: str
    role: str
    overall_score: float
    created_at: str
    questions: list[dict]


# ── Compare ──────────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):
    company1: str
    company2: str


class CompareResponse(BaseModel):
    company1: str
    company2: str
    company1_requirements: str
    company2_requirements: str
    comparison: str


# ── Roadmap ──────────────────────────────────────────────────────────────────

class RoadmapRequest(BaseModel):
    company: str
    days: int = 30

class RoadmapOut(BaseModel):
    id: str
    user_id: str
    company: str
    content: str
    created_at: str

class RoadmapUpdateRequest(BaseModel):
    content: str

class RoadmapListResponse(BaseModel):
    roadmaps: list[RoadmapOut]

class RoadmapResponse(BaseModel):
    roadmap: RoadmapOut

class RoadmapAIEditRequest(BaseModel):
    prompt: str



# ── Visualize ────────────────────────────────────────────────────────────────

class VisualizeResponse(BaseModel):
    nodes: list[dict]
    edges: list[dict]


# ── Company ──────────────────────────────────────────────────────────────────

class CompanyDeleteResponse(BaseModel):
    message: str
    company: str
