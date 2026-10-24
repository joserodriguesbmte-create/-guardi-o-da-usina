"""
Recalcula pressao_corrigida no historico sf6_leituras.

Para disjuntores com manometro_compensado=True (todos os WIKA atuais):
    pressao_corrigida = pressao_medida  (manometro ja indica 20 degC)

Para disjuntores com manometro_compensado=False:
    pressao_corrigida = pressao_medida * (293.15 / (273.15 + temperatura))

Mostra quantos registros serao alterados e pede confirmacao antes de gravar.
Grava backup CSV dos registros afetados antes de qualquer UPDATE.

Execute (previa):  py -3.12 recalcular_pressao_historico.py
Execute (gravar):  py -3.12 recalcular_pressao_historico.py --aplicar
"""

import sys
import csv
import psycopg2
from datetime import datetime
from zoneinfo import ZoneInfo

from equipamentos import DISJUNTORES, pressao_sf6_referencia

_TZ_BR = ZoneInfo("America/Belem")

DB_HOST = "aws-1-sa-east-1.pooler.supabase.com"
DB_PORT = 6543
DB_NAME = "postgres"
DB_USER = "postgres.stgibmuefxrnistysckt"
DB_PASS = "Guardiao2026."

APLICAR = "--aplicar" in sys.argv


def conectar():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS,
        sslmode="require",
        keepalives=1, keepalives_idle=60,
    )


def main():
    print("Conectando ao banco...")
    c = conectar()
    cur = c.cursor()

    cur.execute("""
        SELECT id, disjuntor, polo, pressao_medida, temperatura,
               pressao_corrigida, data, hora
        FROM sf6_leituras
        ORDER BY data, hora, id
    """)
    rows = cur.fetchall()
    print(f"Total de registros em sf6_leituras: {len(rows)}")

    alteracoes = []
    sem_dj = set()

    for row in rows:
        rid, dj, polo, p_med, t_med, p_cor_atual, data, hora = row

        if p_med is None:
            continue

        cfg = DISJUNTORES.get(dj, {})
        if dj and not cfg:
            sem_dj.add(dj)

        compensado = cfg.get("manometro_compensado", True)
        t_uso = float(t_med) if t_med is not None else 20.0

        p_novo = pressao_sf6_referencia(float(p_med), t_uso, compensado)
        p_atual = round(float(p_cor_atual), 3) if p_cor_atual is not None else None

        if p_atual != p_novo:
            alteracoes.append({
                "id": rid,
                "disjuntor": dj,
                "polo": polo,
                "data": data,
                "hora": str(hora)[:5],
                "pressao_medida": float(p_med),
                "temperatura": t_med,
                "pressao_corrigida_atual": p_atual,
                "pressao_corrigida_nova": p_novo,
                "delta": round(p_novo - (p_atual or 0), 4),
                "manometro_compensado": compensado,
            })

    if sem_dj:
        print(f"\nAviso: disjuntores nao cadastrados em equipamentos.py: {sem_dj}")
        print("  Esses registros usaram manometro_compensado=True (padrao).")

    print(f"\nRegistros que serao alterados: {len(alteracoes)} de {len(rows)}")

    if not alteracoes:
        print("Nenhum registro precisa ser atualizado. Banco ja esta correto.")
        cur.close(); c.close()
        return

    # Amostra
    print("\nAmostra dos primeiros 10 registros afetados:")
    print(f"{'ID':>6}  {'Disjuntor':<12}  {'Polo':<8}  {'Data':<12}  "
          f"{'P.Med':>7}  {'T(C)':>5}  {'P.Atual':>8}  {'P.Nova':>8}  {'Delta':>8}")
    print("-" * 92)
    for a in alteracoes[:10]:
        print(f"{a['id']:>6}  {str(a['disjuntor']):<12}  {str(a['polo']):<8}  "
              f"{str(a['data']):<12}  {a['pressao_medida']:>7.3f}  "
              f"{str(a['temperatura'] or ''):>5}  "
              f"{str(a['pressao_corrigida_atual'] or ''):>8}  "
              f"{a['pressao_corrigida_nova']:>8.3f}  {a['delta']:>+8.4f}")
    if len(alteracoes) > 10:
        print(f"  ... e mais {len(alteracoes) - 10} registro(s).")

    # Backup CSV
    ts = datetime.now(_TZ_BR).strftime("%Y%m%d_%H%M%S")
    backup_path = f"backup_sf6_pressao_{ts}.csv"
    campos = ["id", "disjuntor", "polo", "data", "hora", "pressao_medida",
              "temperatura", "pressao_corrigida_atual", "pressao_corrigida_nova",
              "delta", "manometro_compensado"]
    with open(backup_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(alteracoes)
    print(f"\nBackup gravado: {backup_path}")

    if not APLICAR:
        print("\nPREVIA — nenhuma alteracao foi feita no banco.")
        print("Rode com --aplicar para gravar:")
        print("  py -3.12 recalcular_pressao_historico.py --aplicar")
        cur.close(); c.close()
        return

    # Confirmacao interativa
    resp = input(f"\nConfirmar UPDATE de {len(alteracoes)} registro(s) no banco? [s/N] ").strip().lower()
    if resp != "s":
        print("Cancelado. Nenhuma alteracao gravada.")
        cur.close(); c.close()
        return

    print("\nAtualizando...")
    ok = 0
    for a in alteracoes:
        try:
            cur.execute(
                "UPDATE sf6_leituras SET pressao_corrigida = %s WHERE id = %s",
                (a["pressao_corrigida_nova"], a["id"])
            )
            ok += 1
        except Exception as e:
            print(f"  Erro no id={a['id']}: {e}")

    c.commit()
    print(f"\nConcluido: {ok}/{len(alteracoes)} registro(s) atualizado(s).")
    print(f"Backup disponivel em: {backup_path}")
    cur.close(); c.close()


if __name__ == "__main__":
    main()
