import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from a .env file next to this script.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Read DB connection settings from environment.
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST", "localhost")   # sensible default
port = os.getenv("DB_PORT", "3306")        # default MySQL port
db_name = os.getenv("DB_NAME")

# Fail fast if required values are missing.
missing = [k for k, v in {
    "DB_USER": user, "DB_PASSWORD": password, "DB_NAME": db_name
}.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
    f"@{host}:{port}/{db_name}"
)

engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
