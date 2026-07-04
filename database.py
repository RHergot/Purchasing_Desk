from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import config # <--- CORRECTION ICI

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()