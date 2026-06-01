"""
Corrige pressão de alarme SF6 conforme placa do disjuntor Siemens 3AP1 FG:
- Pressão nominal:          6,0 bar
- Baixa pressão 1º estágio: 5,2 bar (ALARME)
- Baixa pressão 2º estágio: 5,0 bar (BLOQUEIO)
"""
import psycopg2

DB_URL = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

tags = ["PMDJ6-01","PMDJ6-02","PMDJ6-03","PMDJ6-04","PMDJ6-05"]

c = psycopg2.connect(DB_URL)
cur = c.cursor()
for tag in tags:
    cur.execute("""UPDATE equipamentos SET
        pressao_nominal  = 6.0,
        pressao_alarme   = 5.2,
        pressao_bloqueio = 5.0,
        fabricante = 'Siemens',
        modelo     = '3AP1 FG',
        ano_fabricacao = '2013',
        tensao_nominal = 245,
        corrente_nominal = 3150,
        observacao = 'Placa: IEC 62271-100 | SF6 20C: Nom=6.0 Alarm=5.2 Bloq=5.0 | Corrente=3150A | Icc=40kA | Massa gas=18kg'
        WHERE tag = %s""", (tag,))
    print(f"OK: {tag} — alarme corrigido para 5,2 bar")

c.commit(); cur.close(); c.close()
print("\nTodos os disjuntores atualizados com valores reais da placa.")
