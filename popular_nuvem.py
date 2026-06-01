"""
Popula o banco PostgreSQL na nuvem com todos os equipamentos.
Execute: py -3.12 popular_nuvem.py
"""
import os, psycopg2

DB_URL = "postgresql://postgres:minhaCasa%232026@db.stgibmuefxrnistysckt.supabase.co:5432/postgres?sslmode=require"

DISJUNTORES = [
    ("Disjuntor SF6","PMDJ6-01","Disjuntor Bay 01PUL","ABB","LTB 245E2",230,6.0,5.5,5.0,"Bay 01PUL","Subestacao 230kV",1),
    ("Disjuntor SF6","PMDJ6-02","Disjuntor Vao Linha (3 polos separados)","ABB","LTB 245E2",230,6.0,5.5,5.0,"Vao Linha","Subestacao 230kV",3),
    ("Disjuntor SF6","PMDJ6-03","Disjuntor Bay 02PVL","ABB","LTB 245E2",230,6.0,5.5,5.0,"Bay 02PVL","Subestacao 230kV",1),
    ("Disjuntor SF6","PMDJ6-04","Disjuntor Vao Trafo","ABB","LTB 245E2",230,6.0,5.5,5.0,"Vao Trafo","Subestacao 230kV",1),
    ("Disjuntor SF6","PMDJ6-05","Disjuntor Bay 03PVL","ABB","LTB 245E2",230,6.0,5.5,5.0,"Bay 03PVL","Subestacao 230kV",1),
]

SECCIONADORAS = [
    ("Seccionadora","PMCA6-01","PMCA - Chave de Conexao 01","Siemens","LAV",245,"Bay 01PUL","Subestacao 230kV",1),
    ("Seccionadora","PMCA6-02","PMCA - Chave de Conexao 02","Siemens","LAV",245,"Bay 02PVL","Subestacao 230kV",1),
    ("Seccionadora","PMCA6-03","PMCA - Chave de Conexao 03","Siemens","LAV",245,"Acoplamento","Subestacao 230kV",1),
    ("Seccionadora","PMCA6-04","PMCA - Chave de Conexao 04","Siemens","LAV",245,"Vao Trafo","Subestacao 230kV",1),
    ("Seccionadora","PMCA6-05","PMCA - Chave de Conexao 05","Siemens","LAV",245,"Bay 03PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-01","PMSD - Seccionadora de Disjuntor 01","Siemens","LAV",245,"Bay 01PUL","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-02","PMSD - Seccionadora de Disjuntor 02","Siemens","LAV",245,"Vao Linha","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-03","PMSD - Seccionadora de Disjuntor 03","Siemens","LAV",245,"Bay 02PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-04","PMSD - Seccionadora de Disjuntor 04","Siemens","LAV",245,"Bay 02PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-05","PMSD - Seccionadora de Disjuntor 05","Siemens","LAV",245,"Vao Trafo","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-06","PMSD - Seccionadora de Disjuntor 06","Siemens","LAV",245,"Bay 03PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSD6-07","PMSD - Seccionadora de Disjuntor 07","Siemens","LAV",245,"Bay 03PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-01","PMSB - Seccionadora de Barra 01","Siemens","LAV",245,"Bay 01PUL","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-02","PMSB - Seccionadora de Barra 02","Siemens","LAV",245,"Bay 01PUL","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-03","PMSB - Seccionadora de Barra 03","Siemens","LAV",245,"Vao Linha","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-04","PMSB - Seccionadora de Barra 04","Siemens","LAV",245,"Vao Linha","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-05","PMSB - Seccionadora de Barra 05","Siemens","LAV",245,"Bay 02PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-06","PMSB - Seccionadora de Barra 06","Siemens","LAV",245,"Bay 02PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-07","PMSB - Seccionadora de Barra 07","Siemens","LAV",245,"Vao Trafo","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-08","PMSB - Seccionadora de Barra 08","Siemens","LAV",245,"Vao Trafo","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-09","PMSB - Seccionadora de Barra 09","Siemens","LAV",245,"Bay 03PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSB6-10","PMSB - Seccionadora de Barra 10","Siemens","LAV",245,"Bay 03PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSY6-01","PMSY - Seccionadora de Terra 01","Siemens","LAV",245,"Bay 01PUL","Subestacao 230kV",1),
    ("Seccionadora","PMSY6-02","PMSY - Seccionadora de Terra 02","Siemens","LAV",245,"Vao Linha","Subestacao 230kV",1),
    ("Seccionadora","PMSY6-03","PMSY - Seccionadora de Terra 03","Siemens","LAV",245,"Bay 02PVL","Subestacao 230kV",1),
    ("Seccionadora","PMSY6-04","PMSY - Seccionadora de Terra 04","Siemens","LAV",245,"Vao Trafo","Subestacao 230kV",1),
    ("Seccionadora","PMSY6-05","PMSY - Seccionadora de Terra 05","Siemens","LAV",245,"Bay 03PVL","Subestacao 230kV",1),
]

c = psycopg2.connect(DB_URL)
cur = c.cursor()
ok = 0

for d in DISJUNTORES:
    try:
        cur.execute("""INSERT INTO equipamentos
            (tipo,tag,descricao,fabricante,modelo,tensao_nominal,
             pressao_nominal,pressao_alarme,pressao_bloqueio,
             localizacao,sistema,num_polos,ativo)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            ON CONFLICT (tag) DO NOTHING""", d)
        if cur.rowcount: print(f"OK DJ: {d[1]}"); ok+=1
        else: print(f"JA EXISTE: {d[1]}")
    except Exception as e: print(f"ERRO {d[1]}: {e}"); c.rollback()

for s in SECCIONADORAS:
    try:
        cur.execute("""INSERT INTO equipamentos
            (tipo,tag,descricao,fabricante,modelo,tensao_nominal,
             localizacao,sistema,num_polos,ativo)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
            ON CONFLICT (tag) DO NOTHING""", s)
        if cur.rowcount: print(f"OK SEC: {s[1]}"); ok+=1
        else: print(f"JA EXISTE: {s[1]}")
    except Exception as e: print(f"ERRO {s[1]}: {e}"); c.rollback()

c.commit(); cur.close(); c.close()
print(f"\n{ok} equipamento(s) cadastrado(s) na nuvem.")
