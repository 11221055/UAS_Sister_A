import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    REDIS_URL = os.getenv("REDIS_URL", "")
    WORKERS = int(os.getenv("WORKERS", "4"))
    QUEUE_NAME = os.getenv("QUEUE_NAME", "logq")

settings = Settings()
