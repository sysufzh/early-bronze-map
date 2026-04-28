from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# Use psycopg (v3) driver: postgresql+psycopg://
db_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
