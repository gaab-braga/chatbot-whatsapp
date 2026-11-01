import smtplib
import os
from email.mime.text import MIMEText

def enviar_email(assunto, corpo):
    """Envia um e-mail usando as credenciais do ambiente."""
    try:
        msg = MIMEText(corpo)
        msg["Subject"] = assunto
        msg["From"] = os.getenv("EMAIL_USER")
        msg["To"] = os.getenv("EMAIL_TO") # Usar um destinatário separado

        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT"))
        email_user = os.getenv("EMAIL_USER")
        email_pass = os.getenv("EMAIL_PASS")

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")