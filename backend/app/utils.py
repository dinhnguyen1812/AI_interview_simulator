from openai import OpenAI
import os

client = OpenAI()

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
    except RateLimitError:
        return "Error: OpenAI API quote exceeded. Please check your API key builling status."
