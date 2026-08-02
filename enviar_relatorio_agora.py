"""
Gera e envia o relatorio mensal completo por e-mail.
Execute: py -3.12 enviar_relatorio_agora.py
"""
import os, json
os.environ["DATABASE_URL"] = "postgresql://postgres.stgibmuefxrnistysckt:Guardiao2026.@aws-1-sa-east-1.pooler.supabase.com:6543/postgres"

from datetime import date
import pandas as pd
from database import (carregar_sf6, carregar_temps, carregar_pendencias,
                      carregar_inspecoes, carregar_equipamentos,
                      carregar_operacoes, carregar_contadores, carregar_fotos,
                      carregar_config)
from email_report import (gerar_html_relatorio, enviar_relatorio,
                          carregar_config_email, fig_para_base64, html_para_pdf)

# ── Período ──────────────────────────────────────────────────────────────────
d_ini = date(2026, 7, 1)
d_fim = date(2026, 7, 31)
mes   = "Julho/2026"

print("Carregando dados do banco...")

df_sf6_r    = carregar_sf6(data_ini=d_ini, data_fim=d_fim)
df_sf6_hist = carregar_sf6()  # histórico completo
df_t_r      = carregar_temps(data_ini=d_ini, data_fim=d_fim)
df_p_r      = carregar_pendencias()
df_i_r      = carregar_inspecoes(data_ini=d_ini, data_fim=d_fim)
df_i_sec    = carregar_inspecoes(sistema="Seccionadora",  data_ini=d_ini, data_fim=d_fim)
df_i_sf6vis = carregar_inspecoes(sistema="Disjuntor SF6", data_ini=d_ini, data_fim=d_fim)
df_i_trafo  = carregar_inspecoes(sistema="Transformador", data_ini=d_ini, data_fim=d_fim)
df_ops_r    = carregar_operacoes()
df_secs     = carregar_equipamentos("Seccionadora")
df_cnt_r    = carregar_contadores(data_ini=d_ini, data_fim=d_fim)

print(f"  SF6: {len(df_sf6_r)} leituras")
print(f"  Temperaturas: {len(df_t_r)} registros")
print(f"  Pendencias: {len(df_p_r)} total")
print(f"  Inspeções: {len(df_i_r)} registros")
print(f"  Seccionadoras: {len(df_i_sec)} inspeções")
print(f"  Contadores: {len(df_cnt_r)} registros")

# ── KPIs ─────────────────────────────────────────────────────────────────────
n_alarmes_sf6   = len(df_sf6_r[df_sf6_r.status_sf6 != "NORMAL"]) if not df_sf6_r.empty else 0
pend_abertas    = len(df_p_r[df_p_r.status == "Aberta"])          if not df_p_r.empty else 0
pend_concluidas = len(df_p_r[df_p_r.status == "Concluída"])       if not df_p_r.empty else 0

# ── SF6 — última leitura por disjuntor/polo ───────────────────────────────────
sf6_tab = []
if not df_sf6_r.empty:
    _ult = df_sf6_r.sort_values("created_at").groupby(["disjuntor","polo"]).last().reset_index()
    sf6_tab = _ult.to_dict("records")

# ── SF6 — inspeção visual (última por disjuntor) ─────────────────────────────
sf6_visual = []
if not df_i_sf6vis.empty:
    for _, _r in df_i_sf6vis.sort_values("data").groupby("item").last().reset_index().iterrows():
        try:
            _itens = json.loads(_r.observacao.split(" | ")[0]) if _r.observacao else {}
        except Exception:
            _itens = {}
        sf6_visual.append({"disjuntor": _r["item"], "status": _r.status,
                            "data": _r.data, "itens": _itens})

# ── Operações no período ──────────────────────────────────────────────────────
df_ops_periodo = df_ops_r[(df_ops_r.data >= str(d_ini)) & (df_ops_r.data <= str(d_fim))] if not df_ops_r.empty else pd.DataFrame()
ops_lista = df_ops_periodo.to_dict("records") if not df_ops_periodo.empty else []

# ── Trafo ─────────────────────────────────────────────────────────────────────
trafo_tab = df_t_r.sort_values("data", ascending=False).head(15).to_dict("records") if not df_t_r.empty else []
trafo_insp = {}
if not df_i_trafo.empty:
    _ult_tr = df_i_trafo.sort_values("data").iloc[-1]
    try:
        trafo_insp = json.loads(_ult_tr.observacao) if _ult_tr.observacao else {}
        trafo_insp["data"]   = _ult_tr.data
        trafo_insp["status"] = _ult_tr.status
    except Exception:
        trafo_insp = {"data": _ult_tr.data, "status": _ult_tr.status}

# ── Inspeções complementares ──────────────────────────────────────────────────
_IC_MAP = [
    ("Para-raios 230kV",    "PARA-RAIOS-230kV"),
    ("Sala Elétrica da SE", "SALA-ELETRICA-SE"),
    ("Cúbilo de 13.8kV",   "CUBILO-13.8kV-SE"),
]
insp_complement = []
for _nome, _tag in _IC_MAP:
    _df_tag = df_i_r[df_i_r.item == _tag] if not df_i_r.empty else pd.DataFrame()
    if not _df_tag.empty:
        _ult_ic = _df_tag.sort_values("data").iloc[-1]
        try:
            _dados_ic = json.loads(_ult_ic.observacao) if _ult_ic.observacao else {}
        except Exception:
            _dados_ic = {}
        insp_complement.append({"nome": _nome, "data": _ult_ic.data,
                                 "status": _ult_ic.status, "dados": _dados_ic})
    else:
        insp_complement.append({"nome": _nome, "data": "—",
                                 "status": "Sem registro", "dados": {}})

# ── Seccionadoras ─────────────────────────────────────────────────────────────
nok_sec_lista = df_i_sec[df_i_sec.status == "NOK"].to_dict("records") if not df_i_sec.empty else []
todas_sec_lista = []
if not df_i_sec.empty:
    for _, _rs in df_i_sec.sort_values("data").groupby("item").last().reset_index().iterrows():
        todas_sec_lista.append({"item": _rs["item"], "data": _rs.data, "status": _rs.status})
insp_sec_count  = len(df_i_sec["item"].unique()) if not df_i_sec.empty else 0
total_sec_count = len(df_secs) if not df_secs.empty else 27

cnt_lista = df_cnt_r.to_dict("records") if not df_cnt_r.empty else []

# ── Fotos: busca mês atual + mês anterior (fotos da aba Relatório ficam com d_fim do período) ──
print("Carregando fotos do período...")
from datetime import timedelta
_foto_ini = (d_ini.replace(day=1) - timedelta(days=1)).replace(day=1)  # 1º do mês anterior
df_fotos = carregar_fotos(data_ini=str(_foto_ini), data_fim=str(d_fim))
fotos_dados = []
for _, _fr in df_fotos.head(10).iterrows():
    if _fr.foto_base64:
        fotos_dados.append({"base64": _fr.foto_base64, "legenda": _fr.legenda or ""})
print(f"  Fotos encontradas (jul+ago): {len(fotos_dados)}")

# ── Montar dados completos ────────────────────────────────────────────────────
dados = {
    "operador": "José Aparecido",
    "nivel":    "SR",
    "mes":      mes,
    "sistemas": ["Subestação 230kV", "Sala Elétrica da SE", "Cúbilo de 13.8kV da SE"],
    "resumo": {
        "leituras_sf6":          len(df_sf6_r),
        "alarmes_sf6":           n_alarmes_sf6,
        "temp_registradas":      len(df_t_r),
        "inspecoes":             len(df_i_r),
        "pendencias_abertas":    pend_abertas,
        "pendencias_concluidas": pend_concluidas,
    },
    "observacoes":     carregar_config("rel_obs_guardiao", ""),
    "acoes":           carregar_config("rel_acoes_destaque", ""),
    "img_sf6":         "",
    "img_temp":        "",
    "pendencias":      df_p_r[df_p_r.status != "Concluída"].to_dict("records") if not df_p_r.empty else [],
    "sf6_tabela":      sf6_tab,
    "sf6_visual":      sf6_visual,
    "operacoes":       ops_lista,
    "sec_resumo": {
        "total":         total_sec_count,
        "inspecionadas": insp_sec_count,
        "nok":           nok_sec_lista,
        "todas":         todas_sec_lista,
    },
    "trafo_tabela":    trafo_tab,
    "trafo_insp":      trafo_insp,
    "insp_complement": insp_complement,
    "contadores":      cnt_lista,
    "fotos":           fotos_dados,
    "sf6_historico":   df_sf6_hist.to_dict("records") if not df_sf6_hist.empty else [],
}

print("Gerando HTML do relatório...")
html = gerar_html_relatorio(dados, usar_cid=bool(fotos_dados))

print("Gerando PDF para anexo...")
anexos = []
try:
    pdf = html_para_pdf(dados)
    if pdf:
        anexos.append(("Relatorio_Agosto_2026.pdf", pdf))
        print("  PDF gerado com sucesso")
except Exception as e:
    print(f"  PDF não gerado: {e}")

print("Enviando por e-mail...")
cfg = carregar_config_email()
# TESTE — envia apenas para Jose Santos
cfg["destinatarios"] = ["josesantos@norteenergiasa.com.br"]
assunto = f"[TESTE] Relatorio Guardiao da Usina — {mes}"
ok, msg = enviar_relatorio(cfg, html, assunto,
                           fotos=fotos_dados if fotos_dados else None,
                           anexos=anexos if anexos else None)
status = "ENVIADO COM SUCESSO" if ok else "ERRO"
print(f"{status}: {msg.encode('ascii','ignore').decode()}")
