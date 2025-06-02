from fastapi import FastAPI, HTTPException
from app.models import InterviewRequest, SessionData, FeedbackRequest
from app.utils import (
    generate_interview_question,
    generate_session_id,
    log_interaction,
    sessions,
    generate_feedback,
    create_session,
    get_session_log
)
from app.db import database

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AI Interview Simulator is running 🚀"}

@app.post("/interview/question")
async def get_question(req: InterviewRequest):
    session_id = req.session_id or generate_session_id()
    question = generate_interview_question(req.topic, req.difficulty)

    if not req.session_id:
        await create_session(session_id)

    await log_interaction(session_id, question)
    return {"question": question, "session_id": session_id}

@app.get("/session/{session_id}")
async def get_session_log_route(session_id: str):
    records = await get_session_log(session_id)
    return {"session_id": session_id, "interactions": records}

@app.post("/interview/feedback")
def give_feedback(req: FeedbackRequest):
    session = sessions.get(req.session_id)
    if not session or not session.interactions:
        raise HTTPException(status_code=404, detail="Session not found or has no questions")
    
    last_interaction = session.interactions[-1]
    last_interaction.answer = req.answer
    
    feedback, score = generate_feedback(last_interaction.question, req.answer)
    last_interaction.feedback = feedback
    last_interaction.score = score
    
    return {
        "feedback": feedback,
        "score": score
    }

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


