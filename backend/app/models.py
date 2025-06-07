from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db import metadata

class InterviewRequest(BaseModel):
    role: str
    experience: str
    tech_stack: str
    difficulty: str
    session_id: Optional[str] = None

class Interaction(BaseModel):
    question: str
    answer: Optional[str] = None
    timestamp: datetime
    feedback: Optional[str] = None
    score: Optional[int] = None  # 1–10 scale

class SessionData(BaseModel):
    session_id: str
    interactions: List[Interaction] = []

class FeedbackRequest(BaseModel):
    session_id: str
    answer: str

class AdviceRequest(BaseModel):
    session_id: str

sessions_table = Table(
    "sessions",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_email", String, ForeignKey("users.email")),
    Column("created_at", DateTime, server_default=func.now()),
)

interactions_table = Table(
    "interactions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("session_id", String, ForeignKey("sessions.id")),
    Column("question", Text),
    Column("answer", Text),
    Column("feedback", Text),
    Column("score", Integer),
    Column("timestamp", DateTime, default=datetime.utcnow),
)

users_table = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, index=True),
    Column("password", String),
    Column("role", String, nullable=True),
    Column("experience", String, nullable=True),
    Column("tech_stack", String, nullable=True),
)

