import smtplib, ssl, base64, io, json, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.json")

def salvar_config_email(cfg: dict):
    with open(CFG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def carregar_config_email() -> dict:
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH) as f:
            return json.load(f)
    return {
        "smtp_server": "smtp.gmail.com", "smtp_port": 587,
        "email_remetente": "", "senha_app": "",
        "destinatarios": [],
        "assunto_padrao": "Relatório Mensal — Guardião da Usina | UHE Belo Monte"
    }

def fig_para_base64(fig) -> str:
    try:
        img_bytes = fig.to_image(format="png", width=900, height=320, engine="kaleido")
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        return ""

def foto_para_base64(foto_bytes: bytes) -> str:
    return base64.b64encode(foto_bytes).decode("utf-8")

_CSS = """
body{font-family:'Segoe UI',Arial,sans-serif;background:#f8fafc;color:#1e293b;margin:0;padding:0;}
.wrap{max-width:900px;margin:0 auto;padding:0 0 40px;}
.capa{background:linear-gradient(135deg,#0c2340,#1e3a5f);padding:36px 40px;}
.capa-title{color:#f1f5f9;font-size:1.8rem;font-weight:900;margin:0 0 4px;}
.capa-sub{color:#60a5fa;font-size:0.9rem;}
.capa-info{display:flex;gap:32px;margin-top:20px;flex-wrap:wrap;}
.capa-item{color:#94a3b8;font-size:0.85rem;}
.capa-item b{color:#f1f5f9;}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px;}
.chip{background:#0f3460;color:#60a5fa;border:1px solid #1e5a96;border-radius:20px;padding:3px 14px;font-size:0.78rem;font-weight:600;}
.secao{background:#fff;border:1px solid #e2e8f0;border-radius:12px;margin:16px 24px;padding:22px 26px;box-shadow:0 1px 4px rgba(0,0,0,0.06);}
.secao-titulo{font-size:1rem;font-weight:800;color:#0f3460;border-bottom:2px solid #e2e8f0;padding-bottom:10px;margin:0 0 16px;}
.kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;}
.kpi-box{background:#f1f5f9;border-radius:10px;padding:14px;text-align:center;border-top:3px solid #3b82f6;}
.kpi-n{font-size:2rem;font-weight:900;color:#0f3460;}
.kpi-l{font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:4px;}
table{width:100%;border-collapse:collapse;font-size:0.83rem;}
th{background:#f1f5f9;color:#0f3460;text-align:left;padding:9px 12px;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.5px;}
td{padding:8px 12px;border-bottom:1px solid #f1f5f9;color:#475569;}
tr:last-child td{border-bottom:none;}
.ok{color:#10b981;font-weight:700;}.alarm{color:#f59e0b;font-weight:700;}
.bloq{color:#ef4444;font-weight:700;}.nok{color:#ef4444;font-weight:700;}
.grafico{width:100%;border-radius:8px;margin:8px 0;}
.obs-box{background:#f8fafc;border-left:4px solid #3b82f6;border-radius:4px;padding:14px 16px;color:#475569;font-size:0.88rem;line-height:1.7;white-space:pre-wrap;}
.foto-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px;margin-top:8px;}
.foto-item img{width:100%;border-radius:8px;border:1px solid #e2e8f0;}
.foto-legenda{font-size:0.75rem;color:#64748b;margin-top:4px;text-align:center;}
.assin{display:flex;gap:40px;margin-top:20px;flex-wrap:wrap;}
.assin-linha{border-bottom:1px solid #cbd5e1;width:220px;margin-bottom:6px;height:36px;}
.assin-nome{color:#475569;font-size:0.85rem;font-weight:600;}
.assin-cargo{color:#94a3b8;font-size:0.75rem;}
.rodape{text-align:center;color:#94a3b8;font-size:0.75rem;margin:24px;padding-top:16px;border-top:1px solid #e2e8f0;}
.barra{height:12px;background:#f1f5f9;border-radius:8px;overflow:hidden;}
.barra-fill{height:100%;border-radius:8px;background:#06b6d4;}
"""

def gerar_html_relatorio(dados: dict) -> str:
    operador      = dados.get("operador", "—")
    nivel         = dados.get("nivel", "—")
    mes           = dados.get("mes", "—")
    sistemas      = dados.get("sistemas", [])
    resumo        = dados.get("resumo", {})
    obs           = dados.get("observacoes", "")
    acoes         = dados.get("acoes", "")
    img_sf6       = dados.get("img_sf6", "")
    img_temp      = dados.get("img_temp", "")
    pendencias    = dados.get("pendencias", [])
    sf6_tabela    = dados.get("sf6_tabela", [])
    sec_resumo    = dados.get("sec_resumo", {})
    trafo_tab     = dados.get("trafo_tabela", [])
    fotos         = dados.get("fotos", [])
    gerado_em     = datetime.now().strftime("%d/%m/%Y às %H:%M")

    def badge(s):
        s = str(s).upper()
        if "NORMAL" in s or s == "OK": return f"<span class='ok'>{s}</span>"
        if "ALARME" in s:              return f"<span class='alarm'>{s}</span>"
        if "BLOQUEIO" in s or "NOK" in s: return f"<span class='bloq'>{s}</span>"
        return f"<span>{s}</span>"

    # KPIs
    kpi_cores = ["#3b82f6","#ef4444","#f59e0b","#10b981","#8b5cf6","#06b6d4"]
    kpi_itens = [
        (resumo.get("leituras_sf6",0),         "Leituras SF6"),
        (resumo.get("alarmes_sf6",0),          "Alarmes SF6"),
        (resumo.get("temp_registradas",0),     "Reg. Temperatura"),
        (resumo.get("inspecoes",0),            "Inspeções"),
        (resumo.get("pendencias_abertas",0),   "Pend. Abertas"),
        (resumo.get("pendencias_concluidas",0),"Pend. Concluídas"),
    ]
    kpis_html = "".join([
        f"<div class='kpi-box' style='border-top-color:{kpi_cores[i]}'>"
        f"<div class='kpi-n' style='color:{kpi_cores[i]}'>{n}</div>"
        f"<div class='kpi-l'>{l}</div></div>"
        for i,(n,l) in enumerate(kpi_itens)])

    # SF6 tabela
    sf6_rows = "".join([
        f"<tr><td><b>{r.get('disjuntor','')}</b></td><td>{r.get('polo','')}</td>"
        f"<td>{r.get('pressao_medida','')}</td><td>{r.get('temperatura','')}°C</td>"
        f"<td><b>{r.get('pressao_corrigida','')}</b></td>"
        f"<td>{r.get('data','')} {str(r.get('hora',''))[:5]}</td>"
        f"<td>{badge(r.get('status_sf6',''))}</td></tr>"
        for r in sf6_tabela])

    # Seccionadoras
    total_sec = sec_resumo.get("total", 0)
    insp_sec  = sec_resumo.get("inspecionadas", 0)
    nok_sec   = sec_resumo.get("nok", [])
    pct_sec   = int(insp_sec/total_sec*100) if total_sec else 0
    nok_rows  = "".join([
        f"<tr><td>{n.get('data','')}</td><td><b>{n.get('item','')}</b></td>"
        f"<td>{n.get('observacao','—')}</td></tr>" for n in nok_sec])

    # Trafo temperatura
    trafo_rows = "".join([
        f"<tr><td>{r.get('data','')} {str(r.get('hora',''))[:5]}</td>"
        f"<td>{r.get('ponto','')}</td>"
        f"<td><b>{r.get('temperatura','')}°C</b></td>"
        f"<td>{r.get('limite_max','')}°C</td>"
        f"<td>{badge(r.get('status',''))}</td></tr>"
        for r in trafo_tab])

    # Pendências
    def cor_p(p): return "#ef4444" if p=="Alta" else "#f59e0b" if p=="Média" else "#10b981"
    pend_rows = "".join([
        f"<tr><td>{p.get('data_abertura','')}</td><td>{p.get('sistema','')}</td>"
        f"<td>{str(p.get('descricao',''))[:60]}</td>"
        f"<td style='color:{cor_p(p.get(\"prioridade\",\"\"))};font-weight:700'>{p.get('prioridade','')}</td>"
        f"<td>{p.get('nota_sap','—')}</td>"
        f"<td style='color:#f59e0b'>{p.get('status','')}</td></tr>"
        for p in pendencias])

    # Fotos
    fotos_html = ""
    if fotos:
        items = "".join([
            f"<div class='foto-item'>"
            f"<img src='data:image/jpeg;base64,{f[\"base64\"]}' alt='foto'>"
            f"<div class='foto-legenda'>{f.get('legenda','')}</div></div>"
            for f in fotos])
        fotos_html = f"<div class='foto-grid'>{items}</div>"

    secao_num = 7 if fotos else 6

    return f"""<!DOCTYPE html><html lang="pt-BR"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relatório Guardião — {mes}</title><style>{_CSS}</style></head><body>
<div class="wrap">

<div class="capa">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">
    <div>
      <div class="capa-title">🛡️ Relatório Mensal — Guardião da Usina</div>
      <div class="capa-sub">Norte Energia S.A. · UHE Belo Monte · Subestação 230kV</div>
    </div>
    <div style="text-align:right;color:#475569;font-size:0.8rem">
      Gerado em: {gerado_em}<br>Referência: <b style="color:#f1f5f9">{mes}</b>
    </div>
  </div>
  <div class="capa-info">
    <div class="capa-item">Guardião: <b>{operador}</b></div>
    <div class="capa-item">Nível: <b style="color:#60a5fa">{nivel}</b></div>
  </div>
  <div class="chips">{''.join([f'<span class="chip">⚡ {s}</span>' for s in sistemas])}</div>
</div>

<div class="secao">
  <div class="secao-titulo">📊 1. Resumo Executivo</div>
  <div class="kpi-grid">{kpis_html}</div>
</div>

<div class="secao">
  <div class="secao-titulo">⚡ 2. Monitoramento SF6 — Disjuntores 230kV</div>
  <p style="font-size:0.82rem;color:#64748b;margin:0 0 12px">
    Siemens 3AP1 FG · Pressão nominal: <b>6,0 bar</b> ·
    Alarme 1°estágio: <b style="color:#f59e0b">5,2 bar</b> ·
    Bloqueio 2°estágio: <b style="color:#ef4444">5,0 bar</b> · Corrigida a 20°C
  </p>
  <table><tr><th>Disjuntor</th><th>Polo</th><th>P.Medida</th><th>Temp.</th>
    <th>P.Corrigida 20°C</th><th>Data/Hora</th><th>Status</th></tr>
    {sf6_rows or '<tr><td colspan="7" style="color:#94a3b8;text-align:center">Sem leituras no período</td></tr>'}
  </table>
  <br>{'<img class="grafico" src="data:image/png;base64,' + img_sf6 + '">' if img_sf6 else '<p style="color:#94a3b8;font-style:italic">Gráfico indisponível.</p>'}
</div>

<div class="secao">
  <div class="secao-titulo">🔌 3. Inspeções de Seccionadoras</div>
  <div style="display:flex;gap:16px;align-items:center;margin-bottom:14px;flex-wrap:wrap">
    <div class="kpi-box" style="border-top-color:#06b6d4;min-width:110px">
      <div class="kpi-n" style="color:#06b6d4">{insp_sec}/{total_sec}</div>
      <div class="kpi-l">Inspecionadas</div></div>
    <div class="kpi-box" style="border-top-color:{'#ef4444' if nok_sec else '#10b981'};min-width:110px">
      <div class="kpi-n" style="color:{'#ef4444' if nok_sec else '#10b981'}">{len(nok_sec)}</div>
      <div class="kpi-l">NOK</div></div>
    <div style="flex:1;min-width:180px">
      <div class="barra"><div class="barra-fill" style="width:{pct_sec}%"></div></div>
      <div style="font-size:0.75rem;color:#64748b;margin-top:4px">{pct_sec}% concluído</div>
    </div>
  </div>
  {f'<table><tr><th>Data</th><th>Seccionadora</th><th>Observação</th></tr>{nok_rows}</table>'
   if nok_rows else '<p style="color:#10b981;font-style:italic">✅ Nenhuma seccionadora com NOK no período.</p>'}
</div>

<div class="secao">
  <div class="secao-titulo">🌡️ 4. Temperatura — Transformador TR-SE-01 Toshiba</div>
  {'<img class="grafico" src="data:image/png;base64,' + img_temp + '">' if img_temp else ''}
  {f'<br><table><tr><th>Data/Hora</th><th>Ponto</th><th>Temperatura</th><th>Limite</th><th>Status</th></tr>{trafo_rows}</table>'
   if trafo_rows else '<p style="color:#94a3b8;font-style:italic">Sem registros de temperatura no período.</p>'}
</div>

<div class="secao">
  <div class="secao-titulo">⚠️ 5. Pendências em Aberto</div>
  {f'<table><tr><th>Data</th><th>Sistema</th><th>Descrição</th><th>Prioridade</th><th>SAP</th><th>Status</th></tr>{pend_rows}</table>'
   if pend_rows else '<p style="color:#10b981;font-style:italic">✅ Sem pendências abertas.</p>'}
</div>

{'<div class="secao"><div class="secao-titulo">📷 6. Registro Fotográfico</div>' + fotos_html + '</div>' if fotos else ''}

<div class="secao">
  <div class="secao-titulo">📝 {secao_num}. Observações e Ações de Destaque</div>
  <p style="font-size:0.8rem;color:#64748b;margin:0 0 8px;font-weight:600">Observações do Guardião</p>
  <div class="obs-box">{obs or 'Sem observações adicionais.'}</div>
  {f'<p style="font-size:0.8rem;color:#64748b;margin:16px 0 8px;font-weight:600">🏆 Ações de Destaque</p><div class="obs-box">{acoes}</div>' if acoes else ''}
</div>

<div class="secao">
  <div class="secao-titulo">✍️ Assinatura</div>
  <div class="assin">
    <div><div class="assin-linha"></div>
      <div class="assin-nome">{operador}</div>
      <div class="assin-cargo">Guardião — Nível {nivel}</div></div>
    <div><div class="assin-linha"></div>
      <div class="assin-nome">Data</div>
      <div class="assin-cargo">______/______/______</div></div>
  </div>
</div>

<div class="rodape">
  🛡️ Guardião da Usina · Norte Energia — UHE Belo Monte<br>
  Relatório gerado automaticamente em {gerado_em}
</div>
</div></body></html>"""


def enviar_relatorio(cfg: dict, html: str, assunto: str, anexos: list = None) -> tuple:
    try:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = assunto
        msg["From"]    = cfg["email_remetente"]
        msg["To"]      = ", ".join(cfg["destinatarios"])

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(html, "html", "utf-8"))
        msg.attach(alt)

        if anexos:
            for nome, conteudo in anexos:
                parte = MIMEBase("application", "octet-stream")
                parte.set_payload(conteudo)
                encoders.encode_base64(parte)
                parte.add_header("Content-Disposition", f'attachment; filename="{nome}"')
                msg.attach(parte)

        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as srv:
            srv.ehlo(); srv.starttls(context=context)
            srv.login(cfg["email_remetente"], cfg["senha_app"])
            srv.sendmail(cfg["email_remetente"], cfg["destinatarios"], msg.as_string())
        return True, f"✅ E-mail enviado para: {', '.join(cfg['destinatarios'])}"
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Erro de autenticação. Verifique o e-mail e Senha de App."
    except smtplib.SMTPConnectError:
        return False, "❌ Não foi possível conectar ao servidor SMTP."
    except Exception as e:
        return False, f"❌ Erro: {str(e)}"
