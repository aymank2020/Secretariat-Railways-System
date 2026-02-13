import os

SECRET_KEY = os.getenv("SECRET_KEY", "railways-secretariat-secret-key-2024-very-secure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./secretariat.db")
