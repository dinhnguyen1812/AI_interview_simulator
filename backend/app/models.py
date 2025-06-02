from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Text
from app.db import metadata
from datetime import datetime

class InterviewRequest(BaseModel):
    topic: str
    difficulty: str = "medium"
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

sessions_table = Table(
    "sessions",
    metadata,
    Column("id", String, primary_key=True),
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
