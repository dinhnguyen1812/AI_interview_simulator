from fastapi import FastAPI, HTTPException, Query, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models import InterviewRequest, FeedbackRequest, AdviceRequest
from app.models import (
    interactions_table, 
    sessions_table, 
    users_table, 
    user_skills_table, 
    user_skill_history_table
)
from app.auth import manager
from app.constants import skills
from app.utils import (
    generate_interview_question,
    generate_session_id,
    log_interaction,
    generate_feedback,
    create_session,
    generate_advice,
    extract_skill_scores
)
from app.db import database

from datetime import datetime
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

    # Create session if not exists
    if not req.session_id:
        await create_session(session_id, user.email)

        # Update user profile with the latest role, experience, tech_stack
        await database.execute(
            users_table.update()
            .where(users_table.c.email == user.email)
            .values(
                role=req.role,
                experience=req.experience,
                tech_stack=req.tech_stack
            )
        )

    # Get last answer if any
    query = interactions_table.select().where(
        interactions_table.c.session_id == session_id
    ).order_by(interactions_table.c.timestamp.desc()).limit(1)

    last_interaction = await database.fetch_one(query)
    last_answer = last_interaction["answer"] if last_interaction else None

    # Generate question with context
    question = await generate_interview_question(
        role=req.role,
        experience=req.experience,
        tech_stack=req.tech_stack,
        difficulty=req.difficulty,
        last_answer=last_answer
    )

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

    # Fetch previous skill scores for this user
    # Assuming you have user email available (e.g. via token)
    prev_scores_query = user_skills_table.select().where(
        user_skills_table.c.user_email == user.email
    )
    rows = await database.fetch_all(prev_scores_query)
    last_skill_scores = {row['skill_name']: row['score'] for row in rows} if rows else {}
    # Initialize missing skills with 0
    for skill in skills:
        last_skill_scores.setdefault(skill, 0.0)

    # Extract updated skill scores
    updated_skill_scores = await extract_skill_scores(req.answer, last_skill_scores)

    # Upsert updated skill scores into DB
    for skill, new_score in updated_skill_scores.items():
        now = datetime.utcnow()

        # 1. Insert into history
        await database.execute(
            user_skill_history_table.insert().values(
                user_email=user.email,
                skill_name=skill,
                score=new_score,
                timestamp=now
            )
        )

        # 2. Upsert current skill snapshot
        stmt = pg_insert(user_skills_table).values(
            user_email=user.email,
            skill_name=skill,
            score=new_score,
            updated_at=now
        ).on_conflict_do_update(
            index_elements=["user_email", "skill_name"],
            set_={
                "score": new_score,
                "updated_at": now
            }
        )
        await database.execute(stmt)

    return {
        "feedback": feedback,
        "score": score,
        "skills": updated_skill_scores
    }

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

    return {
        "msg": "Login successful",
        "role": db_user["role"],
        "experience": db_user["experience"],
        "tech_stack": db_user["tech_stack"],
    }

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

@app.post("/interview/advice")
async def give_advice(user=Depends(manager)):
    # Fetch all session IDs for this user
    session_query = sessions_table.select().where(sessions_table.c.user_email == user.email)
    sessions = await database.fetch_all(session_query)
    session_ids = [s["id"] for s in sessions]

    if not session_ids:
        raise HTTPException(status_code=404, detail="No sessions found for this user.")

    # Fetch all interactions tied to those sessions
    interaction_query = interactions_table.select().where(
        interactions_table.c.session_id.in_(session_ids)
    ).order_by(interactions_table.c.timestamp.asc())
    interactions = await database.fetch_all(interaction_query)

    if not interactions:
        raise HTTPException(status_code=404, detail="No interactions found.")

    # Use the utility function
    advice = await generate_advice(interactions)

    return {"advice": advice}

