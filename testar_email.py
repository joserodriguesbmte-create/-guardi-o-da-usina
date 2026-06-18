import smtplib, ssl, json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

with open("email_config.json") as f:
    cfg = json.load(f)
print(f"Testando: {cfg['email_remetente']} para {cfg['destinatarios']}")

html = """<h2>🛡️ Teste — Guardião da Usina</h2>
<p>E-mail de teste enviado com sucesso!</p>
<p>Sistema: Norte Energia — UHE Belo Monte | SE 230kV</p>"""

msg = MIMEMultipart("alternative")
msg["Subject"] = "🧪 Teste — Guardião da Usina"
msg["From"]    = cfg["email_remetente"]
msg["To"]      = ", ".join(cfg["destinatarios"])
msg.attach(MIMEText(html, "html", "utf-8"))

try:
    context = ssl.create_default_context()
    with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"]) as srv:
        srv.ehlo()
        srv.starttls(context=context)
        srv.login(cfg["email_remetente"], cfg["senha_app"])
        srv.sendmail(cfg["email_remetente"], cfg["destinatarios"], msg.as_string())
    print("OK: E-mail enviado para", cfg["destinatarios"])
except Exception as e:
    print("ERRO:", e)
