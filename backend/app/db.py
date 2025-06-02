from sqlalchemy import create_engine, MetaData
from databases import Database
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/interviews")

database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)

