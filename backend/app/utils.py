from openai import OpenAI
from datetime import datetime
from zoneinfo import ZoneInfo
from app.models import SessionData, Interaction, sessions_table, interactions_table
from app.db import database
from app.constants import skills
from typing import Optional
import json
import uuid

import re

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

async def generate_interview_question(
    role: str,
    experience: str,
    tech_stack: str,
    difficulty: str,
    last_answer: str = None,
    model: str = "gpt-3.5-turbo"
) -> str:
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a professional technical interviewer. "
                    f"Generate a {difficulty} interview question for a {role} "
                    f"with {experience} of experience using {tech_stack}."
                )
            }
        ]

        if last_answer:
            messages.append({
                "role": "user",
                "content": (
                    f"The candidate just gave this answer: {last_answer}. "
                    f"Please ask a follow-up question related to it, but not repeating the last one."
                )
            })
        else:
            messages.append({
                "role": "user",
                "content": (
                    f"Please ask a {difficulty} interview question for a {role} with {experience} "
                    f"experience using {tech_stack}."
                )
            })

        response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating question: {e}"

def generate_feedback(question: str, answer: str, model: str = "gpt-3.5-turbo") -> tuple[str, int]:
    try:
        response = client.chat.completions.create(
            model=model,
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

        feedback_match = re.search(r"Feedback:\s*(.*)", content, re.IGNORECASE)
        feedback = feedback_match.group(1).strip() if feedback_match else "No feedback found."

        score_match = re.search(r"Score:\s*(\d+)", content, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 0

        return feedback, score

    except Exception as e:
        return f"Feedback error: {e}", 0

async def create_session(session_id: str, user_email: Optional[str] = None):
    jst_now = datetime.now(ZoneInfo("Asia/Tokyo"))
    query = sessions_table.insert().values(
        id=session_id,
        user_email=user_email,
        created_at=jst_now
    )
    await database.execute(query)

async def log_interaction(session_id: str, question: str, answer: str = None):
    query = interactions_table.insert().values(
        session_id=session_id,
        question=question,
        answer=answer,
        timestamp=datetime.utcnow()
    )
    await database.execute(query)

async def generate_advice(interactions: list[dict], model: str = "gpt-3.5-turbo") -> str:
    from openai import OpenAI
    client = OpenAI()

    if not interactions:
        return "No interaction history available for advice."

    history_text = ""
    for i in interactions:
        history_text += (
            f"\nQuestion: {i['question']}\n"
            f"Answer: {i['answer'] or '(no answer)'}\n"
            f"Feedback: {i['feedback'] or '(no feedback)'}\n"
        )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional technical interview coach. "
                        "Analyze the candidate’s interview history and give short advice about each of their weaknesses "
                        "and how they can improve for their target role."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Here is the candidate’s interview history:\n{history_text}\n\n"
                        "Based on this, what are their weaknesses and how can they improve?"
                    )
                }
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating advice: {e}"

async def extract_skill_scores(
    answer: str,
    last_skill_scores: dict[str, float],
    model: str = "gpt-4o-mini"
) -> dict[str, float]:
    """
    Use the OpenAI API to extract scores for each skill based on the given answer
    and previous skill scores.
    Returns a dict of skill_name -> updated score (0 to 10).
    """
    last_scores_json = json.dumps(last_skill_scores)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a technical interview evaluator. "
                "Given the candidate's answer and their previous skill scores (0-10), "
                "evaluate and update the scores for each of the following skills:\n" +
                "\n".join(f"- {skill}" for skill in skills) +
                "\nScores should be between 0 and 10."
            )
        },
        {
            "role": "user",
            "content": (
                f"Candidate answer:\n{answer}\n\n"
                f"Previous skill scores:\n{last_scores_json}\n\n"
                "Please provide updated skill scores in JSON format as "
                "{skill_name: score, ...} with numeric scores."
            )
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )
    content = response.choices[0].message.content.strip()

    # Parse JSON safely
    try:
        updated_scores = json.loads(content)
        # Validate keys and score ranges
        updated_scores = {
            k: max(0, min(10, float(v))) for k, v in updated_scores.items() if k in skills
        }
        return updated_scores
    except Exception as e:
        # fallback to last scores if parse error
        return last_skill_scores
