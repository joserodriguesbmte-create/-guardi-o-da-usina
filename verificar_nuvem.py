import psycopg2

c = psycopg2.connect(
    host="db.stgibmuefxrnistysckt.supabase.co",
    port=5432, dbname="postgres",
    user="postgres", password="minhaCasa#2026",
    sslmode="require", connect_timeout=15
)
cur = c.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tabelas = cur.fetchall()
print("Tabelas criadas no Supabase:")
for t in tabelas:
    cur.execute(f"SELECT COUNT(*) FROM {t[0]}")
    n = cur.fetchone()[0]
    print(f"  {t[0]}: {n} registros")
cur.close(); c.close()
