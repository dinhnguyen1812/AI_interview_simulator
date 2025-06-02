from fastapi import FastAPI
from app.models import InterviewRequest
from app.utils import (
    generate_interview_question,
    generate_session_id,
    log_interaction,
    sessions
)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AI Interview Simulator is running 🚀"}

@app.post("/interview/question")
def get_question(req: InterviewRequest):
    session_id = req.session_id or generate_session_id()
    question = generate_interview_question(req.topic, req.difficulty)
    log_interaction(session_id, question)
    return {"question": question, "session_id": session_id}

@app.get("/session/{session_id}")
def get_session_log(session_id: str):
    session = sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}
    return session

