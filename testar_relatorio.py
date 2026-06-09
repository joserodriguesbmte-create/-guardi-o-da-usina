"""
Gera e envia o relatório mensal de teste com fotos reais da SE.
Execute: py -3.12 testar_relatorio.py
"""
import os, sys, json, base64
import psycopg2
import pandas as pd
from datetime import date

# ── paths
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from email_report import (gerar_html_relatorio, enviar_relatorio,
                           carregar_config_email, foto_para_base64)

DB_URL = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

# ── Período
D_INI = "2026-06-01"
D_FIM = "2026-06-30"
MES   = "Junho/2026"

# ── Fotos para incluir no relatório
FOTOS_PATHS = [
    (r"C:\Users\joser\Downloads\WhatsApp Image 2026-06-08 at 18.36.02 (2).jpeg",
     "Painel de contadores — Disjuntor 3 polos (P1LA/B/V, P1LT, P2)"),
    (r"C:\Users\joser\Downloads\WhatsApp Image 2026-06-08 at 18.36.02 (1).jpeg",
     "TM1 Treetech (OTI/WTI) e K60 AVR — Transformador TR-SE-01"),
    (r"C:\Users\joser\Downloads\WhatsApp Image 2026-06-08 at 18.36.02.jpeg",
     "TM1 Treetech — Detalhe OTI 42,9°C / WTI 57,8°C"),
    (r"C:\Users\joser\Downloads\Captura de tela 2026-06-09 125551.png",
     "Unifilar Simplificado — Setor 230kV UHE Belo Monte"),
]

def carregar_foto(path, legenda):
    try:
        with open(path, "rb") as f:
            return {"base64": foto_para_base64(f.read()), "legenda": legenda}
    except FileNotFoundError:
        print(f"  [aviso] Foto nao encontrada: {path}")
        return None

# ── Carregar dados do banco
print("Carregando dados do banco...")
c = psycopg2.connect(DB_URL, sslmode="require")
c.set_client_encoding("UTF8")

df_sf6   = pd.read_sql_query(f"SELECT * FROM sf6_leituras WHERE data>='{D_INI}' AND data<='{D_FIM}' ORDER BY data", c)
df_temps = pd.read_sql_query(f"SELECT * FROM temperaturas WHERE data>='{D_INI}' AND data<='{D_FIM}'", c)
df_pend  = pd.read_sql_query("SELECT * FROM pendencias ORDER BY created_at DESC", c)
df_insp  = pd.read_sql_query(f"SELECT * FROM inspecoes WHERE data>='{D_INI}' AND data<='{D_FIM}'", c)
df_ops   = pd.read_sql_query("SELECT * FROM operacoes_dj ORDER BY data DESC", c)
df_secs  = pd.read_sql_query("SELECT * FROM equipamentos WHERE tipo='Seccionadora' AND ativo=1", c)
c.close()

print(f"  SF6: {len(df_sf6)} leituras | Temps: {len(df_temps)} | Pendencias: {len(df_pend)} | Inspecoes: {len(df_insp)}")

# ── Montar dados do relatório
import json as _j

# SF6 ultima leitura por disjuntor/polo
sf6_tab = []
if not df_sf6.empty:
    sf6_tab = df_sf6.sort_values("created_at").groupby(["disjuntor","polo"]).last().reset_index().to_dict("records")

# SF6 visual
sf6_visual = []
df_sf6vis = df_insp[df_insp.sistema == "Disjuntor SF6"] if not df_insp.empty else pd.DataFrame()
if not df_sf6vis.empty:
    for _, r in df_sf6vis.sort_values("data").groupby("item").last().reset_index().iterrows():
        try: itens = _j.loads(r.observacao.split(" | ")[0]) if r.observacao else {}
        except: itens = {}
        sf6_visual.append({"disjuntor": r.item, "status": r.status, "data": r.data, "itens": itens})

# Trafo
trafo_tab = df_temps.sort_values("data", ascending=False).head(15).to_dict("records") if not df_temps.empty else []
trafo_insp = {}
df_trafo_i = df_insp[df_insp.sistema == "Transformador"] if not df_insp.empty else pd.DataFrame()
if not df_trafo_i.empty:
    ult = df_trafo_i.sort_values("data").iloc[-1]
    try: trafo_insp = _j.loads(ult.observacao) if ult.observacao else {}
    except: trafo_insp = {}
    trafo_insp["data"] = ult.data; trafo_insp["status"] = ult.status

# Pendências
pend_abertas    = df_pend[df_pend.status == "Aberta"] if not df_pend.empty else pd.DataFrame()
n_pend_ab       = len(pend_abertas)
n_pend_conc     = len(df_pend[df_pend.status == "Concluida"]) if not df_pend.empty else 0
n_alarmes_sf6   = len(df_sf6[df_sf6.status_sf6 != "NORMAL"]) if not df_sf6.empty else 0
insp_sec        = df_insp[df_insp.sistema == "Seccionadora"] if not df_insp.empty else pd.DataFrame()
nok_sec         = insp_sec[insp_sec.status == "NOK"].to_dict("records") if not insp_sec.empty else []
ops_periodo     = df_ops[(df_ops.data >= D_INI) & (df_ops.data <= D_FIM)].to_dict("records") if not df_ops.empty else []

# Fotos
print("Carregando fotos...")
fotos_dados = [f for f in (carregar_foto(p, l) for p, l in FOTOS_PATHS) if f]
print(f"  {len(fotos_dados)} foto(s) carregada(s)")

dados = {
    "operador":  "Jose Aparecido",
    "nivel":     "SR",
    "mes":       MES,
    "sistemas":  ["Subestacao 230kV", "Sala Eletrica da SE"],
    "resumo": {
        "leituras_sf6":          len(df_sf6),
        "alarmes_sf6":           n_alarmes_sf6,
        "temp_registradas":      len(df_temps),
        "inspecoes":             len(df_insp),
        "pendencias_abertas":    n_pend_ab,
        "pendencias_concluidas": n_pend_conc,
    },
    "observacoes": "Relatorio gerado via script de teste — Junho/2026.",
    "acoes":       "",
    "img_sf6":     "",
    "img_temp":    "",
    "pendencias":  df_pend[df_pend.status != "Concluida"].to_dict("records") if not df_pend.empty else [],
    "sf6_tabela":  sf6_tab,
    "sf6_visual":  sf6_visual,
    "operacoes":   ops_periodo,
    "sec_resumo": {
        "total": len(df_secs) if not df_secs.empty else 27,
        "inspecionadas": len(insp_sec["item"].unique()) if not insp_sec.empty else 0,
        "nok": nok_sec,
    },
    "trafo_tabela": trafo_tab,
    "trafo_insp":   trafo_insp,
    "fotos":        fotos_dados,
}

# ── Gerar HTML (para download) e HTML com CID (para e-mail)
print("Gerando HTML...")
html_download = gerar_html_relatorio(dados, usar_cid=False)
html_email    = gerar_html_relatorio(dados, usar_cid=True)

# Salvar HTML localmente para inspecao visual
html_path = os.path.join(os.environ["USERPROFILE"], "Downloads",
                         f"Relatorio_Guardiao_{MES.replace('/','_')}.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_download)
print(f"HTML salvo em: {html_path}")

# ── Enviar por e-mail
cfg = carregar_config_email()
print(f"Enviando para: {cfg.get('destinatarios')} ...")

assunto = f"[TESTE] Relatorio Guardiao da Usina - {MES} | Jose Aparecido"
ok, msg = enviar_relatorio(cfg, html_email, assunto,
                           fotos=fotos_dados if fotos_dados else None)

if ok:
    print(f"E-mail enviado com sucesso!")
    print(f"  Para: {cfg.get('destinatarios')}")
    print(f"  Fotos incluidas: {len(fotos_dados)}")
else:
    print(f"ERRO ao enviar: {msg}")
