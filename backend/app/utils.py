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

