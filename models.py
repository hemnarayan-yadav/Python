from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from database import Base


# A "model" = a Python class that maps to a DB table (ORM = Object Relational Mapper).
# Each class attribute = one column in the table.
class User(Base):
    __tablename__ = "users"  # actual table name in MySQL

    # primary_key=True -> unique row id; index=True speeds up lookups by id.
    id = Column(Integer, primary_key=True, index=True)

    # nullable=False -> column is required (NOT NULL in SQL).
    name = Column(String(100), nullable=False)

    # unique=True -> DB rejects duplicate emails (data integrity at DB level).
    # index=True  -> fast lookup by email.
    email = Column(String(150), unique=True, index=True, nullable=False)

    age = Column(Integer, nullable=False)

    # server_default=func.now() -> MySQL fills this automatically on INSERT.
    # Better than setting it in Python: the DB clock is the single source of truth.
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

