import psycopg2

conn = psycopg2.connect(
    "postgresql://mydatabase_cpj0_user:suPpDNHiKk5i9LHVJW3whDHFFhM5hUTG@dpg-d77vqa6uk2gs73b195tg-a.oregon-postgres.render.com/mydatabase_cpj0"
)

cur = conn.cursor()

# 🔥 ALL TABLES DELETE (clean reset)
cur.execute("""
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
""")

conn.commit()
cur.close()
conn.close()

print("✅ FULL DATABASE RESET DONE")