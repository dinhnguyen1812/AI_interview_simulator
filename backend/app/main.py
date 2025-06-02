from fastapi import FastAPI
from pydantic import BaseModel
from app.utils import generate_interview_question

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AI Interview Simulator is running 🚀"}

class InterviewRequest(BaseModel):
    topic: str
    difficulty: str = "medium"

@app.post("/interview/question")
def get_question(req: InterviewRequest):
    question = generate_interview_question(req.topic, req.difficulty)
    return {"question": question}

