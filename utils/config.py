import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite://data/db.sqlite3")
    ALLOW_ORIGIN = os.getenv("ALLOW_ORIGIN", "")
    WORKERS = int(os.getenv("WORKERS", "4"))
    
    SECRET_KEY = os.getenv("SECRET_KEY", "NodesBoard").encode()
    LOCK_DURATION = int(os.getenv("LOCK_DURATION", "300"))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    TOKEN_EXPIRE_SECONDS = int(os.getenv("TOKEN_EXPIRE_SECONDS", "604800"))
    
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))