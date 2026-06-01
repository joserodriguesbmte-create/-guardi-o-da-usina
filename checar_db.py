import sqlite3
db = sqlite3.connect('guardiao.db')
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    count = db.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
    print(f"{t[0]}: {count} registros")
db.close()
