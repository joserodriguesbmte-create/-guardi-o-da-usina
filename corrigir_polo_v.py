"""
Corrige 'Polo C' -> 'Polo V' nos registros de SF6 existentes.
Execute UMA VEZ: py -3.12 corrigir_polo_v.py
"""
import psycopg2

DB_URL = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

c = psycopg2.connect(DB_URL, sslmode="require")
cur = c.cursor()

cur.execute("UPDATE sf6_leituras SET polo = 'Polo V' WHERE polo = 'Polo C'")
print(f"sf6_leituras: {cur.rowcount} registro(s) corrigido(s)")

c.commit(); cur.close(); c.close()
print("Concluído.")
