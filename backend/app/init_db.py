from app.db import metadata, engine
from app.models import sessions_table, interactions_table

def init_db():
    metadata.create_all(engine)
    print("✅ Database tables created.")

if __name__ == "__main__":
    init_db()

