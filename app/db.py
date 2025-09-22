# app/db.py
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import os

DB_URL = os.getenv("DB_URL", "sqlite:///./stats.db")  # local SQLite file in container/workdir
engine: Engine = create_engine(DB_URL, future=True)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS stats (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          qa_threshold REAL,
          count INTEGER,
          min REAL,
          mean REAL,
          max REAL
        )
        """))
