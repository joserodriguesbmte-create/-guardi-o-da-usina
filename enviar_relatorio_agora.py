"""
Gera e envia o relatorio mensal completo por e-mail.
Execute: py -3.12 enviar_relatorio_agora.py
"""
import os, sys
os.environ["DATABASE_URL"] = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

from datetime import date
import pandas as pd
from database import (carregar_sf6, carregar_temps, carregar_pendencias,
                      carregar_inspecoes, carregar_equipamentos, buscar_equipamento_por_tag)
from email_report import gerar_html_relatorio, enviar_relatorio, carregar_config_email

# Periodo
d_ini = date(2026, 6, 1)
d_fim = date(2026, 6, 30)
mes   = "Junho/2026"

print("Carregando dados do banco...")

df_sf6  = carregar_sf6(data_ini=d_ini, data_fim=d_fim)
df_t    = carregar_temps(data_ini=d_ini, data_fim=d_fim)
df_p    = carregar_pendencias()
df_i    = carregar_inspecoes(data_ini=d_ini, data_fim=d_fim)
df_isec = carregar_inspecoes(sistema="Seccionadora", data_ini=d_ini, data_fim=d_fim)
df_secs = carregar_equipamentos("Seccionadora")

print(f"  SF6: {len(df_sf6)} leituras")
print(f"  Temperaturas: {len(df_t)} registros")
print(f"  Pendencias: {len(df_p)} total")
print(f"  Inspecoes seccionadoras: {len(df_isec)}")

# SF6 — ultima leitura por disjuntor/polo
sf6_tab = []
if not df_sf6.empty:
    ult = df_sf6.sort_values("created_at").groupby(["disjuntor","polo"]).last().reset_index()
    sf6_tab = ult.to_dict("records")

# Trafo
trafo_tab = df_t.sort_values("data", ascending=False).head(15).to_dict("records") if not df_t.empty else []

# Seccionadoras
nok_sec = df_isec[df_isec.status == "NOK"].to_dict("records") if not df_isec.empty else []
insp_count = len(df_isec["item"].unique()) if not df_isec.empty else 0

# Pendencias abertas
n_alarmes = len(df_sf6[df_sf6.status_sf6 != "NORMAL"]) if not df_sf6.empty else 0
pend_aber = len(df_p[df_p.status == "Aberta"])          if not df_p.empty else 0
pend_conc = len(df_p[df_p.status == "Concluida"])       if not df_p.empty else 0

dados = {
    "operador": "Jose Aparecido",
    "nivel":    "SR",
    "mes":      mes,
    "sistemas": ["Subestacao 230kV", "Sala Eletrica da SE", "Cubilo 13.8kV da SE"],
    "resumo": {
        "leituras_sf6":          len(df_sf6),
        "alarmes_sf6":           n_alarmes,
        "temp_registradas":      len(df_t),
        "inspecoes":             len(df_i),
        "pendencias_abertas":    pend_aber,
        "pendencias_concluidas": pend_conc,
    },
    "observacoes":  "Relatorio gerado automaticamente pelo sistema Guardiao da Usina.",
    "acoes":        "",
    "img_sf6":      "",
    "img_temp":     "",
    "pendencias":   df_p[df_p.status != "Concluida"].to_dict("records") if not df_p.empty else [],
    "sf6_tabela":   sf6_tab,
    "sec_resumo": {
        "total":         len(df_secs) if not df_secs.empty else 27,
        "inspecionadas": insp_count,
        "nok":           nok_sec,
    },
    "trafo_tabela": trafo_tab,
    "fotos":        [],
}

print("Gerando HTML do relatorio...")
html = gerar_html_relatorio(dados)

print("Enviando por e-mail...")
cfg = carregar_config_email()
assunto = f"Relatorio Mensal - Guardiao da Usina - {mes}"
ok, msg = enviar_relatorio(cfg, html, assunto)
status = "ENVIADO COM SUCESSO" if ok else "ERRO"
print(f"{status}: {msg.encode('ascii','ignore').decode()}")
