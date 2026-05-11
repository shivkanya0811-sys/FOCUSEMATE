from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database name is exactly 'mydatabase' matching your pgAdmin
DATABASE_URL = "postgresql+asyncpg://postgres.picvsparxrgczvhnrfcw:sumantsahilpriyankapranali@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()