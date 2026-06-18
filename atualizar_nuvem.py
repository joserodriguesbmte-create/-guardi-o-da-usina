import psycopg2

DB_URL = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

tags_sec = [
    "PMCA6-01","PMCA6-02","PMCA6-03","PMCA6-04","PMCA6-05",
    "PMSD6-01","PMSD6-02","PMSD6-03","PMSD6-04","PMSD6-05","PMSD6-06","PMSD6-07",
    "PMSB6-01","PMSB6-02","PMSB6-03","PMSB6-04","PMSB6-05","PMSB6-06",
    "PMSB6-07","PMSB6-08","PMSB6-09","PMSB6-10",
    "PMSY6-01","PMSY6-02","PMSY6-03","PMSY6-04","PMSY6-05",
]

c = psycopg2.connect(DB_URL)
cur = c.cursor()
ok = 0
for tag in tags_sec:
    cur.execute("""UPDATE equipamentos SET
        fabricante='Siemens', modelo='LAV', ano_fabricacao='2013',
        tensao_nominal=245, corrente_nominal=2000, numero_serie='0857/2013',
        observacao='NBR IEC 62271-102/2007 | Contrato:108753 | id:104kA | It/t:40/1kAs | M.Polo:570kg | M.Total:1890kg | MO-c:350Nm/13-15s/104kg | Cmd:125Vcc/Motor:440Vcc/Aquec:220Vca/100W'
        WHERE tag=%s""", (tag,))
    if cur.rowcount: ok += 1

c.commit(); cur.close(); c.close()
print(f"{ok} seccionadoras atualizadas na nuvem.")
