# backend/app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AI Interview Simulator is running 🚀"}

