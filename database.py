import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from a .env file into os.environ.
# Keep secrets (DB password, etc.) out of source code.
load_dotenv()

# Read DB connection settings from environment.
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
host = os.getenv("DB_HOST", "localhost")   # sensible default
port = os.getenv("DB_PORT", "3306")        # default MySQL port
db_name = os.getenv("DB_NAME")

# Fail fast if required values are missing.
# A clear error at startup is better than a confusing crash later.
missing = [k for k, v in {
    "DB_USER": user, "DB_PASSWORD": password, "DB_NAME": db_name
}.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

# Build the SQLAlchemy connection URL.
# Format: dialect+driver://user:password@host:port/database
#
# IMPORTANT: we URL-encode user & password with quote_plus(...).
# If the password contains characters like '@', ':', '/', '#', '?'
# the raw URL would be parsed wrongly (e.g. an '@' in the password
# would be mistaken for the user/host separator -> "Can't connect to
# MySQL server on '123@127.0.0.1'" type errors).
DATABASE_URL = (
    f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
    f"@{host}:{port}/{db_name}"
)

# create_engine -> the low-level connection pool to MySQL.
# echo=True            -> log every SQL statement (great while learning, off in prod).
# pool_pre_ping=True   -> ping the connection before using it. Prevents the famous
#                         "MySQL server has gone away" error when idle connections die.
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)

# SessionLocal is a *factory* that produces DB sessions (one per request).
# autocommit=False -> we control when to commit (safer).
# autoflush=False  -> don't auto-send pending changes on every query.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that every ORM model will inherit from.
Base = declarative_base()