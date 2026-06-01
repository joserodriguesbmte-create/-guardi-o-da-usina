"""
Popula o banco com as seccionadoras reais da SE 230kV.
Execute: py -3.12 popular_seccionadoras.py
"""
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guardiao.db")

SECCIONADORAS = [
    # PMCA - Chaves de Conexao
    {"tag": "PMCA6-01", "descricao": "Chave de Conexao 01", "tipo_sec": "PMCA - Chave de Conexao", "localizacao": "Bay 01PUL"},
    {"tag": "PMCA6-02", "descricao": "Chave de Conexao 02", "tipo_sec": "PMCA - Chave de Conexao", "localizacao": "Bay 02PVL"},
    {"tag": "PMCA6-03", "descricao": "Chave de Conexao 03", "tipo_sec": "PMCA - Chave de Conexao", "localizacao": "Acoplamento"},
    {"tag": "PMCA6-04", "descricao": "Chave de Conexao 04", "tipo_sec": "PMCA - Chave de Conexao", "localizacao": "Vao Trafo"},
    {"tag": "PMCA6-05", "descricao": "Chave de Conexao 05", "tipo_sec": "PMCA - Chave de Conexao", "localizacao": "Bay 03PVL"},

    # PMSD - Seccionadoras de Disjuntor
    {"tag": "PMSD6-01", "descricao": "Seccionadora de Disjuntor 01", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Bay 01PUL"},
    {"tag": "PMSD6-02", "descricao": "Seccionadora de Disjuntor 02", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Vao Linha"},
    {"tag": "PMSD6-03", "descricao": "Seccionadora de Disjuntor 03", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Bay 02PVL"},
    {"tag": "PMSD6-04", "descricao": "Seccionadora de Disjuntor 04", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Bay 02PVL"},
    {"tag": "PMSD6-05", "descricao": "Seccionadora de Disjuntor 05", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Vao Trafo"},
    {"tag": "PMSD6-06", "descricao": "Seccionadora de Disjuntor 06", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Bay 03PVL"},
    {"tag": "PMSD6-07", "descricao": "Seccionadora de Disjuntor 07", "tipo_sec": "PMSD - Seccionadora de Disjuntor", "localizacao": "Bay 03PVL"},

    # PMSB - Seccionadoras de Barra
    {"tag": "PMSB6-01", "descricao": "Seccionadora de Barra 01", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Bay 01PUL"},
    {"tag": "PMSB6-02", "descricao": "Seccionadora de Barra 02", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Bay 01PUL"},
    {"tag": "PMSB6-03", "descricao": "Seccionadora de Barra 03", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Vao Linha"},
    {"tag": "PMSB6-04", "descricao": "Seccionadora de Barra 04", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Vao Linha"},
    {"tag": "PMSB6-05", "descricao": "Seccionadora de Barra 05", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Bay 02PVL"},
    {"tag": "PMSB6-06", "descricao": "Seccionadora de Barra 06", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Bay 02PVL"},
    {"tag": "PMSB6-07", "descricao": "Seccionadora de Barra 07", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Vao Trafo"},
    {"tag": "PMSB6-08", "descricao": "Seccionadora de Barra 08", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Vao Trafo"},
    {"tag": "PMSB6-09", "descricao": "Seccionadora de Barra 09", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Bay 03PVL"},
    {"tag": "PMSB6-10", "descricao": "Seccionadora de Barra 10", "tipo_sec": "PMSB - Seccionadora de Barra", "localizacao": "Bay 03PVL"},

    # PMSY - Seccionadoras de Terra
    {"tag": "PMSY6-01", "descricao": "Seccionadora de Terra 01", "tipo_sec": "PMSY - Seccionadora de Terra", "localizacao": "Bay 01PUL"},
    {"tag": "PMSY6-02", "descricao": "Seccionadora de Terra 02", "tipo_sec": "PMSY - Seccionadora de Terra", "localizacao": "Vao Linha"},
    {"tag": "PMSY6-03", "descricao": "Seccionadora de Terra 03", "tipo_sec": "PMSY - Seccionadora de Terra", "localizacao": "Bay 02PVL"},
    {"tag": "PMSY6-04", "descricao": "Seccionadora de Terra 04", "tipo_sec": "PMSY - Seccionadora de Terra", "localizacao": "Vao Trafo"},
    {"tag": "PMSY6-05", "descricao": "Seccionadora de Terra 05", "tipo_sec": "PMSY - Seccionadora de Terra", "localizacao": "Bay 03PVL"},
]

c = sqlite3.connect(DB)
ok = 0
ja_existe = 0
for s in SECCIONADORAS:
    try:
        c.execute("""INSERT OR IGNORE INTO equipamentos
            (tipo, tag, descricao, localizacao, sistema, tensao_nominal, ativo, num_polos)
            VALUES (?, ?, ?, ?, ?, ?, 1, 1)""",
            ("Seccionadora", s["tag"], f"{s['tipo_sec']} - {s['descricao']}",
             s["localizacao"], "Subestacao 230kV", 230))
        if c.execute("SELECT changes()").fetchone()[0]:
            print(f"OK: {s['tag']} [{s['tipo_sec']}] - {s['localizacao']}")
            ok += 1
        else:
            print(f"JA EXISTE: {s['tag']}")
            ja_existe += 1
    except Exception as e:
        print(f"ERRO em {s['tag']}: {e}")

c.commit()
c.close()
print(f"\n{ok} seccionadora(s) cadastrada(s). {ja_existe} ja existia(m).")
