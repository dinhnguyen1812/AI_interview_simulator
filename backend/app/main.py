from fastapi import FastAPI, HTTPException, Query, Depends, Response
from fastapi.staticfiles import StaticFiles
from app.models import InterviewRequest, FeedbackRequest
from app.models import interactions_table, sessions_table, users_table
from app.auth import manager
from app.utils import (
    generate_interview_question,
    generate_session_id,
    log_interaction,
    generate_feedback,
    create_session
)
from app.db import database
from fastapi.middleware.cors import CORSMiddleware
from passlib.hash import bcrypt
from pydantic import BaseModel

import logging

logger = logging.getLogger("uvicorn")

app = FastAPI()

# Serve HTML from frontend directory
app.mount("/static", StaticFiles(directory="frontend", html=True), name="frontend")

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
async def get_question(req: InterviewRequest, user=Depends(manager)):
    session_id = req.session_id or generate_session_id()
    question = generate_interview_question(req.topic, req.difficulty)

    if not req.session_id:
        await create_session(session_id, user.email)  # ← pass email here

    await log_interaction(session_id, question)
    return {"question": question, "session_id": session_id}

@app.get("/session/{session_id}")
async def get_session_log_route(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user=Depends(manager)
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
async def give_feedback(req: FeedbackRequest, user=Depends(manager)):
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

class UserIn(BaseModel):
    email: str
    password: str

@app.post("/auth/register")
async def register(user: UserIn):
    query = users_table.select().where(users_table.c.email == user.email)
    if await database.fetch_one(query):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = bcrypt.hash(user.password)
    await database.execute(users_table.insert().values(email=user.email, password=hashed_pw))
    return {"msg": "User registered"}

@app.post("/auth/login")
async def login(response: Response, user: UserIn):
    query = users_table.select().where(users_table.c.email == user.email)
    db_user = await database.fetch_one(query)
    if not db_user or not bcrypt.verify(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = manager.create_access_token(data={"sub": user.email})
    manager.set_cookie(response, token)
    return {"msg": "Login successful"}

# Logout endpoint — clear the cookie
@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=manager.cookie_name,      # Typically 'access-token'
        path="/",                     # Must match the login path
    )
    return {"message": "Logged out"}

# Get current user info endpoint
@app.get("/auth/user")
def get_current_user(user=Depends(manager)):
    return {"email": user.email}

@app.get("/user/session")
async def get_session_history(user=Depends(manager)):
    query = sessions_table.select().where(sessions_table.c.user_email == user.email)
    sessions = await database.fetch_all(query)
    
    result = []
    for s in sessions:
        result.append({
            "id": s["id"],
            "user_email": s["user_email"],
            "created_at": s["created_at"].isoformat() if s["created_at"] else None  # include timestamp
        })
    return {"sessions": result}
