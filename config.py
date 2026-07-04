import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

COGNEE_API_KEY: str = os.getenv("COGNEE_API_KEY", "")
COGNEE_BASE_URL: str = os.getenv("COGNEE_BASE_URL", "https://api.cognee.ai")
COGNEE_TENANT_ID: str = os.getenv("COGNEE_TENANT_ID", "")

DATABASE_URL: str = os.getenv("DATABASE_URL", "interview_brain.db")

HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
