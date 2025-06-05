from fastapi_login import LoginManager
from fastapi import HTTPException
from app.models import users_table
from app.db import database
import os
from dotenv import load_dotenv

load_dotenv()
SECRET = os.getenv("SECRET_KEY")

manager = LoginManager(SECRET, token_url="/auth/login", use_cookie=True)
manager.cookie_name = "interview_auth"

@manager.user_loader()
async def load_user(email: str):
    query = users_table.select().where(users_table.c.email == email)
    return await database.fetch_one(query)

