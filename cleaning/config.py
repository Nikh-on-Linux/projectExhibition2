import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/emotion_db"
)
PORT = int(os.getenv("PORT", "5000"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
