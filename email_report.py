import smtplib, ssl, base64, io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Configurações SMTP salvas em arquivo local ────────────────────────────
import json, os
CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.json")

def salvar_config_email(cfg: dict):
    with open(CFG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)

def carregar_config_email() -> dict:
    if os.path.exists(CFG_PATH):
        with open(CFG_PATH) as f:
            return json.load(f)
    return {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "email_remetente": "",
        "senha_app": "",
        "destinatarios": [],
        "assunto_padrao": "Relatório Mensal — Guardião da Usina | UHE Belo Monte"
    }

# ── Gerar gráfico como imagem base64 ────────────────────────────────────
def fig_para_base64(fig) -> str:
    """Converte figura Plotly para imagem PNG em base64 para embed no HTML."""
    try:
        img_bytes = fig.to_image(format="png", width=900, height=350,
                                  engine="kaleido")
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        return ""

# ── Montar HTML do relatório ─────────────────────────────────────────────
def gerar_html_relatorio(dados: dict) -> str:
    operador   = dados.get("operador", "—")
    nivel      = dados.get("nivel", "—")
    mes        = dados.get("mes", "—")
    sistemas   = dados.get("sistemas", [])
    resumo     = dados.get("resumo", {})
    obs        = dados.get("observacoes", "")
    acoes      = dados.get("acoes", "")
    img_sf6    = dados.get("img_sf6", "")
    img_temp   = dados.get("img_temp", "")
    pendencias = dados.get("pendencias", [])
    inspecoes  = dados.get("inspecoes_nok", [])
    gerado_em  = datetime.now().strftime("%d/%m/%Y %H:%M")

    def tag_status(v, ok="NORMAL", cor_ok="#10b981", cor_nok="#ef4444"):
        cor = cor_ok if v == ok else cor_nok
        return f"<span style='color:{cor};font-weight:700'>{v}</span>"

    rows_pend = ""
    for p in pendencias:
        cor_p = "#ef4444" if p.get("prioridade")=="Alta" else "#f59e0b" if p.get("prioridade")=="Média" else "#10b981"
        rows_pend += f"""<tr>
            <td>{p.get('data_abertura','')}</td>
            <td>{p.get('sistema','')}</td>
            <td>{p.get('descricao','')[:60]}</td>
            <td style='color:{cor_p};font-weight:700'>{p.get('prioridade','')}</td>
            <td>{p.get('nota_sap','—')}</td>
            <td style='color:#f59e0b'>{p.get('status','')}</td>
        </tr>"""

    rows_nok = ""
    for n in inspecoes:
        rows_nok += f"""<tr>
            <td>{n.get('data','')}</td>
            <td>{n.get('sistema','')}</td>
            <td>{n.get('item','')[:70]}</td>
            <td style='color:#ef4444;font-weight:700'>❌ NOK</td>
            <td>{n.get('observacao','')}</td>
        </tr>"""

    img_sf6_tag  = f'<img src="data:image/png;base64,{img_sf6}" style="width:100%;border-radius:8px">' if img_sf6 else '<p style="color:#475569;font-style:italic">Sem dados de SF6 no período.</p>'
    img_temp_tag = f'<img src="data:image/png;base64,{img_temp}" style="width:100%;border-radius:8px">' if img_temp else '<p style="color:#475569;font-style:italic">Sem dados de temperatura no período.</p>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#0a0e1a; color:#e2e8f0; margin:0; padding:0; }}
  .container {{ max-width:900px; margin:0 auto; padding:24px; }}
  .header {{ background:linear-gradient(135deg,#0c2340,#1e3a5f); border-radius:12px; padding:28px 32px; margin-bottom:24px; }}
  .header h1 {{ color:#f1f5f9; font-size:1.6rem; margin:0 0 6px; }}
  .header .sub {{ color:#60a5fa; font-size:0.9rem; }}
  .section {{ background:#111827; border:1px solid #1e3a5f; border-radius:10px; padding:20px 24px; margin-bottom:16px; }}
  .section h2 {{ color:#60a5fa; font-size:1rem; font-weight:700; margin:0 0 14px; border-bottom:1px solid #1e3a5f; padding-bottom:8px; }}
  .kpi-row {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:8px; }}
  .kpi {{ background:#0a1628; border:1px solid #1e3a5f; border-radius:8px; padding:14px 20px; text-align:center; flex:1; min-width:120px; }}
  .kpi-n {{ font-size:1.8rem; font-weight:900; color:#3b82f6; }}
  .kpi-l {{ font-size:0.72rem; color:#475569; text-transform:uppercase; letter-spacing:1px; margin-top:3px; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
  th {{ background:#0a1628; color:#60a5fa; text-align:left; padding:8px 12px; font-weight:700; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; }}
  td {{ padding:8px 12px; border-bottom:1px solid #1e293b; color:#94a3b8; }}
  tr:hover td {{ background:#0f172a; }}
  .obs-box {{ background:#0a1628; border-left:4px solid #3b82f6; border-radius:4px; padding:14px; color:#94a3b8; font-size:0.88rem; line-height:1.6; }}
  .badge {{ display:inline-block; border-radius:20px; padding:2px 12px; font-size:0.75rem; font-weight:700; }}
  .footer {{ text-align:center; color:#334155; font-size:0.75rem; margin-top:24px; padding-top:16px; border-top:1px solid #1e293b; }}
  .sistemas-list {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:8px; }}
  .sistema-chip {{ background:#0f2744; color:#60a5fa; border:1px solid #1e5a96; border-radius:20px; padding:4px 14px; font-size:0.78rem; font-weight:600; }}
</style>
</head><body>
<div class="container">

  <!-- CABEÇALHO -->
  <div class="header">
    <div style="display:flex;justify-content:space-between;align-items:start">
      <div>
        <h1>🛡️ Relatório Mensal — Guardião da Usina</h1>
        <div class="sub">Norte Energia | UHE Belo Monte | Programa Guardiões</div>
      </div>
      <div style="text-align:right;color:#475569;font-size:0.8rem">
        Gerado em: {gerado_em}<br>
        Referência: <b style="color:#f1f5f9">{mes}</b>
      </div>
    </div>
    <div style="margin-top:16px;display:flex;gap:24px;font-size:0.85rem">
      <span style="color:#94a3b8">Guardião: <b style="color:#f1f5f9">{operador}</b></span>
      <span style="color:#94a3b8">Nível: <b style="color:#60a5fa">{nivel}</b></span>
    </div>
    <div class="sistemas-list">
      {''.join([f'<span class="sistema-chip">⚡ {s}</span>' for s in sistemas])}
    </div>
  </div>

  <!-- KPIs -->
  <div class="section">
    <h2>📊 Resumo do Período</h2>
    <div class="kpi-row">
      <div class="kpi"><div class="kpi-n" style="color:#3b82f6">{resumo.get('leituras_sf6',0)}</div><div class="kpi-l">Leituras SF6</div></div>
      <div class="kpi"><div class="kpi-n" style="color:#ef4444">{resumo.get('alarmes_sf6',0)}</div><div class="kpi-l">Alarmes SF6</div></div>
      <div class="kpi"><div class="kpi-n" style="color:#f59e0b">{resumo.get('temp_registradas',0)}</div><div class="kpi-l">Reg. Temperatura</div></div>
      <div class="kpi"><div class="kpi-n" style="color:#10b981">{resumo.get('inspecoes',0)}</div><div class="kpi-l">Inspeções</div></div>
      <div class="kpi"><div class="kpi-n" style="color:#8b5cf6">{resumo.get('pendencias_abertas',0)}</div><div class="kpi-l">Pendências Abertas</div></div>
      <div class="kpi"><div class="kpi-n" style="color:#06b6d4">{resumo.get('pendencias_concluidas',0)}</div><div class="kpi-l">Pendências Conclídas</div></div>
    </div>
  </div>

  <!-- GRÁFICO SF6 -->
  <div class="section">
    <h2>⚡ Tendência Pressão SF6 — Corrigida a 20°C</h2>
    {img_sf6_tag}
  </div>

  <!-- GRÁFICO TEMPERATURA -->
  <div class="section">
    <h2>🌡️ Tendência Temperatura por Equipamento</h2>
    {img_temp_tag}
  </div>

  <!-- PENDÊNCIAS -->
  <div class="section">
    <h2>⚠️ Pendências em Aberto</h2>
    {"<table><tr><th>Data</th><th>Sistema</th><th>Descrição</th><th>Prioridade</th><th>SAP</th><th>Status</th></tr>" + rows_pend + "</table>" if rows_pend else '<p style="color:#475569;font-style:italic">Sem pendências abertas no período.</p>'}
  </div>

  <!-- ITENS NOK -->
  <div class="section">
    <h2>❌ Itens de Inspeção NOK</h2>
    {"<table><tr><th>Data</th><th>Sistema</th><th>Item</th><th>Status</th><th>Observação</th></tr>" + rows_nok + "</table>" if rows_nok else '<p style="color:#10b981;font-style:italic">✅ Todos os itens inspecionados aprovados no período.</p>'}
  </div>

  <!-- OBSERVAÇÕES -->
  <div class="section">
    <h2>📝 Observações do Guardião</h2>
    <div class="obs-box">{obs or "Sem observações adicionais."}</div>
  </div>

  <!-- AÇÕES DE DESTAQUE -->
  <div class="section">
    <h2>🏆 Ações de Destaque</h2>
    <div class="obs-box">{acoes or "Sem ações de destaque registradas."}</div>
  </div>

  <!-- ASSINATURA -->
  <div class="section" style="border-color:#1e5a96">
    <h2>✍️ Assinatura</h2>
    <div style="display:flex;gap:40px;margin-top:8px">
      <div>
        <div style="border-bottom:1px solid #334155;width:220px;margin-bottom:6px">&nbsp;</div>
        <div style="color:#94a3b8;font-size:0.82rem">{operador}</div>
        <div style="color:#475569;font-size:0.75rem">Guardião — Nível {nivel}</div>
      </div>
      <div>
        <div style="border-bottom:1px solid #334155;width:160px;margin-bottom:6px">&nbsp;</div>
        <div style="color:#94a3b8;font-size:0.82rem">Data</div>
      </div>
    </div>
  </div>

  <div class="footer">
    🛡️ Guardião da Usina | Norte Energia — UHE Belo Monte<br>
    Programa Guardiões da Usina — Relatório gerado automaticamente em {gerado_em}
  </div>
</div>
</body></html>"""
    return html

# ── Enviar e-mail ─────────────────────────────────────────────────────────
def enviar_relatorio(cfg: dict, html: str, assunto: str) -> tuple[bool, str]:
    """Envia e-mail com o relatório HTML. Retorna (sucesso, mensagem)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"]    = cfg["email_remetente"]
        msg["To"]      = ", ".join(cfg["destinatarios"])

        parte_html = MIMEText(html, "html", "utf-8")
        msg.attach(parte_html)

        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_server"], int(cfg["smtp_port"])) as servidor:
            servidor.ehlo()
            servidor.starttls(context=context)
            servidor.login(cfg["email_remetente"], cfg["senha_app"])
            servidor.sendmail(cfg["email_remetente"], cfg["destinatarios"], msg.as_string())

        return True, f"✅ E-mail enviado com sucesso para: {', '.join(cfg['destinatarios'])}"
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Erro de autenticação. Verifique o e-mail e a Senha de App."
    except smtplib.SMTPConnectError:
        return False, "❌ Não foi possível conectar ao servidor SMTP. Verifique sua conexão."
    except Exception as e:
        return False, f"❌ Erro ao enviar: {str(e)}"
