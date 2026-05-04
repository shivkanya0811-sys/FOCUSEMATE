from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database name is exactly 'focusemate' matching your pgAdmin
DATABASE_URL = "postgresql+psycopg2://postgres:Admin@localhost:5432/focusemate"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()