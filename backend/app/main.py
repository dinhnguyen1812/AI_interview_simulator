from fastapi import FastAPI, HTTPException
from app.models import InterviewRequest, FeedbackRequest
from fastapi import Query
# from typing import Optional
from app.models import interactions_table
from app.utils import (
    generate_interview_question,
    generate_session_id,
    log_interaction,
    generate_feedback,
    create_session
)
from app.db import database
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def get_session_log_route(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    query = (
        interactions_table
        .select()
        .where(interactions_table.c.session_id == session_id)
        .order_by(interactions_table.c.timestamp.asc())
        .offset(skip)
        .limit(limit)
    )
    records = await database.fetch_all(query)

    interactions = [
        {
            "question": r["question"],
            "answer": r["answer"],
            "feedback": r["feedback"],
            "score": r["score"],
            "timestamp": r["timestamp"].isoformat() if r["timestamp"] else None,
        }
        for r in records
    ]

    return {
        "session_id": session_id,
        "interactions": interactions,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "count": len(interactions)
        }
    }

@app.post("/interview/feedback")
async def give_feedback(req: FeedbackRequest):
    # Fetch last interaction for session
    query = interactions_table.select().where(
        interactions_table.c.session_id == req.session_id
    ).order_by(interactions_table.c.timestamp.desc()).limit(1)
    
    last_interaction = await database.fetch_one(query)
    
    if not last_interaction:
        raise HTTPException(status_code=404, detail="No questions found for session")

    # Generate feedback and score
    feedback, score = generate_feedback(last_interaction.question, req.answer)

    # Update the last interaction with answer, feedback, score
    update_query = interactions_table.update().where(
        interactions_table.c.id == last_interaction.id
    ).values(
        answer=req.answer,
        feedback=feedback,
        score=score
    )
    await database.execute(update_query)

    return {"feedback": feedback, "score": score}

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


