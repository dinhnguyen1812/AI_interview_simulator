from pydantic import BaseModel
from typing import List, Optional
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

