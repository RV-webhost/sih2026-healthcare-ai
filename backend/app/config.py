import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    _db_url = os.getenv("DATABASE_URL", "sqlite:///healthcare.db")
    if _db_url and _db_url.startswith("postgresql://"):
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    SQLALCHEMY_DATABASE_URI = _db_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

<<<<<<< HEAD
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
=======
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
>>>>>>> origin/main
