from openai import OpenAI
from datetime import datetime
from app.models import SessionData, Interaction
import uuid

client = OpenAI()

# In-memory session store
sessions = {}

def generate_session_id() -> str:
    return str(uuid.uuid4())

def log_interaction(session_id: str, question: str, answer: str = None):
    interaction = Interaction(
        question=question,
        answer=answer,
        timestamp=datetime.utcnow()
    )
    if session_id not in sessions:
        sessions[session_id] = SessionData(session_id=session_id, interactions=[])
    sessions[session_id].interactions.append(interaction)

def generate_interview_question(topic: str, difficulty: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a technical interviewer. Ask a {difficulty} question about {topic}."
                },
                {
                    "role": "user",
                    "content": f"Please ask me a {difficulty} interview question on {topic}."
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

import re

def generate_feedback(question: str, answer: str) -> tuple[str, int]:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer."
                },
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n"
                        f"Answer: {answer}\n"
                        "Please evaluate the answer, give constructive feedback, and rate it from 1 (poor) to 10 (excellent). "
                        "Respond in the format:\nFeedback: <text>\nScore: <number>"
                    )
                }
            ]
        )
        content = response.choices[0].message.content.strip()
        
        # Extract feedback
        feedback_match = re.search(r"Feedback:\s*(.*)", content, re.IGNORECASE)
        feedback = feedback_match.group(1).strip() if feedback_match else "No feedback found."

        # Extract score (first number after "Score:")
        score_match = re.search(r"Score:\s*(\d+)", content, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 0

        return feedback, score

    except Exception as e:
        return f"Feedback error: {e}", 0

