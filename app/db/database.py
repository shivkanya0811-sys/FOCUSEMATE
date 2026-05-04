from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database name is exactly 'mydatabase' matching your pgAdmin
DATABASE_URL = "postgresql+psycopg2://postgres:easy4@localhost:5432/mydatabase"


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()