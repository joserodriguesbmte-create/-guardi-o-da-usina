"""
Popula o banco de dados com os disjuntores reais da SE 230kV.
Execute uma vez: py -3.12 popular_equipamentos.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardiao.db")

DISJUNTORES = [
    {"tipo": "Disjuntor SF6", "tag": "PMDJ6-01", "descricao": "Disjuntor Bay 01PUL",
     "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230,
     "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0,
     "localizacao": "Bay 01PUL", "sistema": "Subestação 230kV", "num_polos": 1},

    {"tipo": "Disjuntor SF6", "tag": "PMDJ6-02", "descricao": "Disjuntor Vão Linha (3 polos separados)",
     "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230,
     "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0,
     "localizacao": "Vao Linha", "sistema": "Subestação 230kV", "num_polos": 3},

    {"tipo": "Disjuntor SF6", "tag": "PMDJ6-03", "descricao": "Disjuntor Bay 02PVL",
     "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230,
     "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0,
     "localizacao": "Bay 02PVL", "sistema": "Subestação 230kV", "num_polos": 1},

    {"tipo": "Disjuntor SF6", "tag": "PMDJ6-04", "descricao": "Disjuntor Vão Trafo",
     "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230,
     "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0,
     "localizacao": "Vao Trafo", "sistema": "Subestação 230kV", "num_polos": 1},

    {"tipo": "Disjuntor SF6", "tag": "PMDJ6-05", "descricao": "Disjuntor Bay 03PVL",
     "fabricante": "ABB", "modelo": "LTB 245E2", "tensao_nominal": 230,
     "pressao_nominal": 6.0, "pressao_alarme": 5.5, "pressao_bloqueio": 5.0,
     "localizacao": "Bay 03PVL", "sistema": "Subestação 230kV", "num_polos": 1},
]

c = sqlite3.connect(DB)

# Garante que a coluna num_polos existe
try:
    c.execute("ALTER TABLE equipamentos ADD COLUMN num_polos INTEGER DEFAULT 1")
    c.commit()
    print("Coluna num_polos adicionada.")
except Exception:
    pass

ok = 0
for dj in DISJUNTORES:
    try:
        c.execute("""INSERT OR IGNORE INTO equipamentos
            (tipo,tag,descricao,fabricante,modelo,tensao_nominal,
             pressao_nominal,pressao_alarme,pressao_bloqueio,
             localizacao,sistema,num_polos,ativo)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,1)""",
            (dj["tipo"], dj["tag"], dj["descricao"], dj["fabricante"],
             dj["modelo"], dj["tensao_nominal"], dj["pressao_nominal"],
             dj["pressao_alarme"], dj["pressao_bloqueio"],
             dj["localizacao"], dj["sistema"], dj["num_polos"]))
        if c.execute("SELECT changes()").fetchone()[0]:
            print(f"OK: {dj['tag']} - {dj['descricao']} ({dj['num_polos']} polo(s))")
            ok += 1
        else:
            print(f"JA EXISTE: {dj['tag']}")
    except Exception as e:
        print(f"ERRO em {dj['tag']}: {e}")
c.commit(); c.close()
print(f"\n{ok} disjuntor(es) cadastrado(s) com sucesso.")

