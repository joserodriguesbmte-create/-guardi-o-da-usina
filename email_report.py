import smtplib, ssl, base64, json, os, io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

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
        "assunto_padrao": "Relatorio Mensal - Guardiao da Usina | UHE Belo Monte"
    }

def fig_para_base64(fig) -> str:
    try:
        img_bytes = fig.to_image(format="png", width=800, height=300, engine="kaleido")
        return base64.b64encode(img_bytes).decode("utf-8")
    except Exception:
        return ""

def foto_para_base64(foto_bytes: bytes) -> str:
    return base64.b64encode(foto_bytes).decode("utf-8")

def html_para_pdf(html: str) -> bytes:
    """Converte HTML para PDF usando xhtml2pdf."""
    from xhtml2pdf import pisa
    buf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=buf)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# HTML compatível com Gmail (layout por tabelas, sem CSS Grid/Flex)
# ─────────────────────────────────────────────────────────────────────────────
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
    gerado_em     = datetime.now().strftime("%d/%m/%Y as %H:%M")

    def badge(s):
        s = str(s).upper()
        cor = "#10b981" if "NORMAL" in s or s == "OK" else \
              "#f59e0b" if "ALARME" in s else \
              "#ef4444" if "BLOQUEIO" in s or "NOK" in s else "#475569"
        return f"<span style='color:{cor};font-weight:700'>{s}</span>"

    # ── CAPA ─────────────────────────────────────────────────────────────────
    chips = "".join([
        f"<span style='background:#1e5a96;color:#ffffff;border-radius:20px;"
        f"padding:3px 12px;font-size:12px;font-weight:600;margin-right:6px;'>⚡ {s}</span>"
        for s in sistemas])

    capa = f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="background:#0c2340;border-radius:12px 12px 0 0;">
      <tr><td style="padding:32px 36px;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
          <tr>
            <td style="vertical-align:top;">
              <div style="font-size:22px;font-weight:900;color:#f1f5f9;margin-bottom:4px;">
                🛡️ Relatorio Mensal — Guardiao da Usina
              </div>
              <div style="font-size:13px;color:#60a5fa;">
                Norte Energia S.A. · UHE Belo Monte · Subestacao 230kV
              </div>
            </td>
            <td align="right" style="vertical-align:top;font-size:11px;color:#64748b;">
              Gerado em: {gerado_em}<br>
              <strong style="color:#f1f5f9;">Ref: {mes}</strong>
            </td>
          </tr>
        </table>
        <div style="margin-top:16px;font-size:13px;color:#94a3b8;">
          Guardiao: <strong style="color:#f1f5f9;">{operador}</strong>
          &nbsp;&nbsp;|&nbsp;&nbsp;
          Nivel: <strong style="color:#60a5fa;">{nivel}</strong>
        </div>
        <div style="margin-top:12px;">{chips}</div>
      </td></tr>
    </table>"""

    # ── KPIs (tabela 3 colunas × 2 linhas) ───────────────────────────────────
    kpi_data = [
        (resumo.get("leituras_sf6", 0),         "Leituras SF6",      "#3b82f6"),
        (resumo.get("alarmes_sf6", 0),           "Alarmes SF6",       "#ef4444"),
        (resumo.get("temp_registradas", 0),      "Reg. Temperatura",  "#f59e0b"),
        (resumo.get("inspecoes", 0),             "Inspecoes",         "#10b981"),
        (resumo.get("pendencias_abertas", 0),    "Pend. Abertas",     "#8b5cf6"),
        (resumo.get("pendencias_concluidas", 0), "Pend. Concluidas",  "#06b6d4"),
    ]

    def kpi_cell(n, label, cor):
        return (f"<td width='33%' style='padding:6px;'>"
                f"<table width='100%' cellpadding='14' cellspacing='0' border='0' "
                f"style='background:#f1f5f9;border-radius:10px;border-top:3px solid {cor};text-align:center;'>"
                f"<tr><td>"
                f"<div style='font-size:28px;font-weight:900;color:{cor};'>{n}</div>"
                f"<div style='font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-top:4px;'>{label}</div>"
                f"</td></tr></table></td>")

    kpi_html = (
        "<table width='100%' cellpadding='0' cellspacing='0' border='0'>"
        "<tr>" + "".join([kpi_cell(*kpi_data[i]) for i in range(3)]) + "</tr>"
        "<tr>" + "".join([kpi_cell(*kpi_data[i]) for i in range(3, 6)]) + "</tr>"
        "</table>"
    )

    # ── SF6 tabela ────────────────────────────────────────────────────────────
    sf6_rows = ""
    for r in sf6_tabela:
        sf6_rows += (
            f"<tr style='border-bottom:1px solid #f1f5f9;'>"
            f"<td style='padding:8px 10px;font-weight:700;color:#0f3460;'>{r.get('disjuntor','')}</td>"
            f"<td style='padding:8px 10px;color:#475569;'>{r.get('polo','')}</td>"
            f"<td style='padding:8px 10px;color:#475569;'>{r.get('pressao_medida','')}</td>"
            f"<td style='padding:8px 10px;color:#475569;'>{r.get('temperatura','')}°C</td>"
            f"<td style='padding:8px 10px;font-weight:700;'>{r.get('pressao_corrigida','')}</td>"
            f"<td style='padding:8px 10px;color:#475569;'>{r.get('data','')} {str(r.get('hora',''))[:5]}</td>"
            f"<td style='padding:8px 10px;'>{badge(r.get('status_sf6',''))}</td>"
            f"</tr>"
        )
    if not sf6_rows:
        sf6_rows = "<tr><td colspan='7' style='padding:12px;text-align:center;color:#94a3b8;font-style:italic;'>Sem leituras no periodo</td></tr>"

    th_style = "padding:9px 10px;background:#f1f5f9;color:#0f3460;font-size:11px;text-transform:uppercase;text-align:left;"
    sf6_table = (
        f"<table width='100%' cellpadding='0' cellspacing='0' border='0' style='border-collapse:collapse;font-size:13px;'>"
        f"<tr><th style='{th_style}'>Disjuntor</th><th style='{th_style}'>Polo</th>"
        f"<th style='{th_style}'>P.Medida</th><th style='{th_style}'>Temp.</th>"
        f"<th style='{th_style}'>P.Corrigida 20°C</th><th style='{th_style}'>Data/Hora</th>"
        f"<th style='{th_style}'>Status</th></tr>{sf6_rows}</table>"
    )

    img_sf6_html = (f"<br><img src='data:image/png;base64,{img_sf6}' "
                    f"width='100%' style='border-radius:8px;display:block;margin-top:8px;'>"
                    if img_sf6 else "<p style='color:#94a3b8;font-style:italic;'>Grafico indisponivel.</p>")

    # ── Seccionadoras ─────────────────────────────────────────────────────────
    total_sec = sec_resumo.get("total", 0)
    insp_sec  = sec_resumo.get("inspecionadas", 0)
    nok_sec   = sec_resumo.get("nok", [])
    pct_sec   = int(insp_sec / total_sec * 100) if total_sec else 0
    pct_w     = max(1, pct_sec)

    nok_rows = ""
    for n in nok_sec:
        nok_rows += (f"<tr><td style='padding:7px 10px;color:#475569;'>{n.get('data','')}</td>"
                     f"<td style='padding:7px 10px;font-weight:700;color:#0f3460;'>{n.get('item','')}</td>"
                     f"<td style='padding:7px 10px;color:#475569;'>{n.get('observacao','—')}</td></tr>")

    sec_nok_table = ""
    if nok_rows:
        sec_nok_table = (
            f"<table width='100%' cellpadding='0' cellspacing='0' border='0' style='font-size:13px;margin-top:10px;'>"
            f"<tr><th style='{th_style}'>Data</th><th style='{th_style}'>Seccionadora</th>"
            f"<th style='{th_style}'>Observacao</th></tr>{nok_rows}</table>")
    else:
        sec_nok_table = "<p style='color:#10b981;font-style:italic;'>Nenhuma seccionadora com NOK no periodo.</p>"

    # ── Temperatura trafo ─────────────────────────────────────────────────────
    trafo_rows = ""
    for r in trafo_tab:
        trafo_rows += (
            f"<tr><td style='padding:7px 10px;color:#475569;'>{r.get('data','')} {str(r.get('hora',''))[:5]}</td>"
            f"<td style='padding:7px 10px;color:#475569;'>{r.get('ponto','')}</td>"
            f"<td style='padding:7px 10px;font-weight:700;'>{r.get('temperatura','')}°C</td>"
            f"<td style='padding:7px 10px;color:#475569;'>{r.get('limite_max','')}°C</td>"
            f"<td style='padding:7px 10px;'>{badge(r.get('status',''))}</td></tr>"
        )
    trafo_table = ""
    if trafo_rows:
        trafo_table = (
            f"<table width='100%' cellpadding='0' cellspacing='0' border='0' style='font-size:13px;margin-top:10px;'>"
            f"<tr><th style='{th_style}'>Data/Hora</th><th style='{th_style}'>Ponto</th>"
            f"<th style='{th_style}'>Temperatura</th><th style='{th_style}'>Limite</th>"
            f"<th style='{th_style}'>Status</th></tr>{trafo_rows}</table>")
    img_temp_html = (f"<br><img src='data:image/png;base64,{img_temp}' "
                     f"width='100%' style='border-radius:8px;display:block;margin-top:8px;'>"
                     if img_temp else "")

    # ── Pendências ────────────────────────────────────────────────────────────
    def cor_prio(p):
        return "#ef4444" if p == "Alta" else "#f59e0b" if p == "Media" else "#10b981"

    pend_rows = ""
    for p in pendencias:
        pri = p.get("prioridade", "")
        pend_rows += (
            f"<tr><td style='padding:7px 10px;color:#475569;'>{p.get('data_abertura','')}</td>"
            f"<td style='padding:7px 10px;color:#475569;'>{p.get('sistema','')}</td>"
            f"<td style='padding:7px 10px;color:#475569;'>{str(p.get('descricao',''))[:60]}</td>"
            f"<td style='padding:7px 10px;font-weight:700;color:{cor_prio(pri)};'>{pri}</td>"
            f"<td style='padding:7px 10px;color:#475569;'>{p.get('nota_sap','—')}</td>"
            f"<td style='padding:7px 10px;color:#f59e0b;'>{p.get('status','')}</td></tr>"
        )
    pend_table = ""
    if pend_rows:
        pend_table = (
            f"<table width='100%' cellpadding='0' cellspacing='0' border='0' style='font-size:13px;'>"
            f"<tr><th style='{th_style}'>Data</th><th style='{th_style}'>Sistema</th>"
            f"<th style='{th_style}'>Descricao</th><th style='{th_style}'>Prioridade</th>"
            f"<th style='{th_style}'>SAP</th><th style='{th_style}'>Status</th></tr>{pend_rows}</table>")
    else:
        pend_table = "<p style='color:#10b981;font-style:italic;'>Sem pendencias abertas.</p>"

    # ── Fotos ─────────────────────────────────────────────────────────────────
    fotos_section = ""
    if fotos:
        fotos_html = ""
        for i in range(0, len(fotos), 2):
            fotos_html += "<tr>"
            for f in fotos[i:i+2]:
                b64 = f.get("base64", "")
                leg = f.get("legenda", "")
                fotos_html += (
                    f"<td width='50%' style='padding:6px;vertical-align:top;'>"
                    f"<img src='data:image/jpeg;base64,{b64}' width='100%' "
                    f"style='border-radius:8px;border:1px solid #e2e8f0;display:block;'>"
                    f"<div style='font-size:11px;color:#64748b;text-align:center;margin-top:4px;'>{leg}</div>"
                    f"</td>")
            if len(fotos[i:i+2]) == 1:
                fotos_html += "<td width='50%'></td>"
            fotos_html += "</tr>"
        fotos_section = secao("📷 6. Registro Fotografico",
                              f"<table width='100%' cellpadding='0' cellspacing='0' border='0'>{fotos_html}</table>")

    num_obs = 7 if fotos else 6

    # ── Helper para seções ────────────────────────────────────────────────────
    def secao(titulo, conteudo):
        return f"""
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;
                      margin-bottom:16px;font-family:Arial,sans-serif;">
          <tr><td style="padding:22px 26px;">
            <div style="font-size:15px;font-weight:800;color:#0f3460;
                        border-bottom:2px solid #e2e8f0;padding-bottom:10px;margin-bottom:16px;">
              {titulo}
            </div>
            {conteudo}
          </td></tr>
        </table>"""

    # ── MONTAGEM FINAL ────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relatorio Guardiao — {mes}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f1f5f9;">
<tr><td align="center" style="padding:20px 10px;">
<table width="680" cellpadding="0" cellspacing="0" border="0" style="max-width:680px;width:100%;">

  <!-- CAPA -->
  <tr><td style="padding-bottom:16px;">{capa}</td></tr>

  <!-- SEÇÃO 1: RESUMO -->
  <tr><td style="padding-bottom:16px;">
    {secao("📊 1. Resumo Executivo", kpi_html)}
  </td></tr>

  <!-- SEÇÃO 2: SF6 -->
  <tr><td style="padding-bottom:16px;">
    {secao("⚡ 2. Monitoramento SF6 — Disjuntores 230kV",
      f"<p style='font-size:12px;color:#64748b;margin:0 0 12px;'>"
      f"Siemens 3AP1 FG · Nominal: <strong>6,0 bar</strong> · "
      f"Alarme 1 est.: <strong style='color:#f59e0b;'>5,2 bar</strong> · "
      f"Bloqueio 2 est.: <strong style='color:#ef4444;'>5,0 bar</strong> · Corrigida 20°C"
      f"</p>{sf6_table}{img_sf6_html}")}
  </td></tr>

  <!-- SEÇÃO 3: SECCIONADORAS -->
  <tr><td style="padding-bottom:16px;">
    {secao("🔌 3. Inspecoes de Seccionadoras",
      f"<table width='100%' cellpadding='0' cellspacing='0' border='0' style='margin-bottom:12px;'><tr>"
      f"<td width='25%' style='padding:4px;'>"
      f"<table width='100%' cellpadding='14' cellspacing='0' border='0' "
      f"style='background:#f1f5f9;border-radius:10px;border-top:3px solid #06b6d4;text-align:center;'>"
      f"<tr><td><div style='font-size:24px;font-weight:900;color:#06b6d4;'>{insp_sec}/{total_sec}</div>"
      f"<div style='font-size:10px;color:#64748b;'>INSPECIONADAS</div></td></tr></table></td>"
      f"<td width='25%' style='padding:4px;'>"
      f"<table width='100%' cellpadding='14' cellspacing='0' border='0' "
      f"style='background:#f1f5f9;border-radius:10px;border-top:3px solid {'#ef4444' if nok_sec else '#10b981'};text-align:center;'>"
      f"<tr><td><div style='font-size:24px;font-weight:900;color:{'#ef4444' if nok_sec else '#10b981'};'>{len(nok_sec)}</div>"
      f"<div style='font-size:10px;color:#64748b;'>NOK</div></td></tr></table></td>"
      f"<td style='padding:4px 4px 4px 12px;vertical-align:middle;'>"
      f"<table width='100%' cellpadding='0' cellspacing='0' border='0'><tr>"
      f"<td style='background:#e2e8f0;border-radius:8px;height:12px;'>"
      f"<table height='12' cellpadding='0' cellspacing='0' border='0' width='{pct_w}%'><tr>"
      f"<td style='background:#06b6d4;border-radius:8px;'></td></tr></table>"
      f"</td></tr></table>"
      f"<div style='font-size:11px;color:#64748b;margin-top:4px;'>{pct_sec}% concluido</div>"
      f"</td></tr></table>{sec_nok_table}")}
  </td></tr>

  <!-- SEÇÃO 4: TEMPERATURA -->
  <tr><td style="padding-bottom:16px;">
    {secao("🌡️ 4. Temperatura — Transformador TR-SE-01 Toshiba",
      img_temp_html + trafo_table if trafo_table else
      img_temp_html + "<p style='color:#94a3b8;font-style:italic;'>Sem registros no periodo.</p>")}
  </td></tr>

  <!-- SEÇÃO 5: PENDÊNCIAS -->
  <tr><td style="padding-bottom:16px;">
    {secao("⚠️ 5. Pendencias em Aberto", pend_table)}
  </td></tr>

  <!-- SEÇÃO 6: FOTOS (se houver) -->
  {'<tr><td style="padding-bottom:16px;">' + fotos_section + '</td></tr>' if fotos else ''}

  <!-- SEÇÃO OBS -->
  <tr><td style="padding-bottom:16px;">
    {secao(f"📝 {num_obs}. Observacoes e Acoes de Destaque",
      f"<p style='font-size:12px;color:#64748b;font-weight:600;margin:0 0 8px;'>Observacoes do Guardiao</p>"
      f"<div style='background:#f8fafc;border-left:4px solid #3b82f6;border-radius:4px;"
      f"padding:14px;font-size:13px;color:#475569;line-height:1.7;white-space:pre-wrap;'>"
      f"{obs or 'Sem observacoes adicionais.'}</div>"
      + (f"<p style='font-size:12px;color:#64748b;font-weight:600;margin:16px 0 8px;'>Acoes de Destaque</p>"
         f"<div style='background:#f8fafc;border-left:4px solid #10b981;border-radius:4px;"
         f"padding:14px;font-size:13px;color:#475569;line-height:1.7;'>{acoes}</div>" if acoes else ""))}
  </td></tr>

  <!-- ASSINATURA -->
  <tr><td style="padding-bottom:16px;">
    {secao("✍️ Assinatura",
      f"<table cellpadding='0' cellspacing='0' border='0' style='margin-top:10px;'><tr>"
      f"<td style='padding-right:40px;'>"
      f"<div style='border-bottom:1px solid #cbd5e1;width:220px;height:40px;margin-bottom:6px;'></div>"
      f"<div style='color:#475569;font-size:14px;font-weight:600;'>{operador}</div>"
      f"<div style='color:#94a3b8;font-size:12px;'>Guardiao — Nivel {nivel}</div></td>"
      f"<td><div style='border-bottom:1px solid #cbd5e1;width:160px;height:40px;margin-bottom:6px;'></div>"
      f"<div style='color:#475569;font-size:14px;font-weight:600;'>Data</div>"
      f"<div style='color:#94a3b8;font-size:12px;'>____/____/______</div></td>"
      f"</tr></table>")}
  </td></tr>

  <!-- RODAPÉ -->
  <tr><td style="text-align:center;padding:16px;color:#94a3b8;font-size:11px;
                 border-top:1px solid #e2e8f0;">
    🛡️ Guardiao da Usina · Norte Energia — UHE Belo Monte<br>
    Relatorio gerado automaticamente em {gerado_em}
  </td></tr>

</table>
</td></tr>
</table>
</body></html>"""

    return html


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
        return True, "E-mail enviado com sucesso para: " + ", ".join(cfg["destinatarios"])
    except smtplib.SMTPAuthenticationError:
        return False, "Erro de autenticacao. Verifique o e-mail e Senha de App."
    except Exception as e:
        return False, f"Erro ao enviar: {str(e)}"
