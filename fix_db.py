import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))

cur = conn.cursor()


cur.execute("""
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
""")

conn.commit()

cur.close()
conn.close()

print("Database Reset Successful")