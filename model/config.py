import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/emotion_db"
)
MODEL_NAME = os.getenv(
    "MODEL_NAME",
    "j-hartmann/emotion-english-distilroberta-base"
)
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
PORT = int(os.getenv("PORT", "4000"))
