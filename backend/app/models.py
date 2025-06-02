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

class SessionData(BaseModel):
    session_id: str
    interactions: List[Interaction] = []

