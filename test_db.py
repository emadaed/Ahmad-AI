import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        dbname="groweasy_dev",
        user="ahmad_ai_readonly",
        password="localonlypass",
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM customers;")
    print("SUCCESS:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("FAILED:", e)
