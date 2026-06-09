"""
Migração: adiciona PMDB6-01 e corrige descrições das PMCA6-xx.
Execute UMA VEZ: py -3.12 corrigir_equipamentos.py
"""
import psycopg2

DB_URL = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

c = psycopg2.connect(DB_URL, sslmode="require")
cur = c.cursor()

# 1. Inserir PMDB6-01 (Disjuntor Acoplamento de Barras — 3 polos separados)
try:
    cur.execute("""
        INSERT INTO equipamentos
            (tipo, tag, descricao, fabricante, modelo, tensao_nominal,
             pressao_nominal, pressao_alarme, pressao_bloqueio,
             localizacao, sistema, num_polos, ativo)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,1)
        ON CONFLICT (tag) DO NOTHING
    """, (
        "Disjuntor SF6",
        "PMDB6-01",
        "Disjuntor Acoplamento de Barras (3 polos separados)",
        "Siemens", "3AP1 FG",
        230, 6.0, 5.2, 5.0,
        "Acoplamento Barras - Bay 01PCB",
        "Subestacao 230kV",
        3
    ))
    print("PMDB6-01:", "INSERIDO" if cur.rowcount else "já existia")
except Exception as e:
    print(f"ERRO PMDB6-01: {e}"); c.rollback()

# 2. Corrigir descrições das PMCA6-xx (Chave de Conexão → Chave de Aterramento)
PMCA_CORRECOES = {
    "PMCA6-01": ("PMCA - Chave de Aterramento 01", "Bay 01PVL"),
    "PMCA6-02": ("PMCA - Chave de Aterramento 02", "Bay 01PCL"),
    "PMCA6-03": ("PMCA - Chave de Aterramento 03", "Bay 02PVL"),
    "PMCA6-04": ("PMCA - Chave de Aterramento 04", "Bay Trafo - 01PCT"),
    "PMCA6-05": ("PMCA - Chave de Aterramento 05", "Bay 03PVL"),
}

for tag, (descricao, localizacao) in PMCA_CORRECOES.items():
    try:
        cur.execute("""
            UPDATE equipamentos
            SET descricao = %s, localizacao = %s
            WHERE tag = %s
        """, (descricao, localizacao, tag))
        print(f"{tag}: {'ATUALIZADO' if cur.rowcount else 'não encontrado'}")
    except Exception as e:
        print(f"ERRO {tag}: {e}"); c.rollback()

c.commit()
cur.close()
c.close()
print("\nMigração concluída.")
