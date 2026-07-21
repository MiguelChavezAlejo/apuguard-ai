import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_password_reset_email(
    recipient_email: str,
    recipient_name: str,
    reset_url: str,
) -> None:
    subject = "Recuperación de contraseña - ApuGuard AI"

    body = f"""
Hola {recipient_name}:

Recibimos una solicitud para restablecer la contraseña de tu cuenta
en ApuGuard AI.

Abre el siguiente enlace:

{reset_url}

El enlace vencerá en {settings.password_reset_expire_minutes} minutos
y solamente podrá utilizarse una vez.

Si no solicitaste este cambio, ignora este mensaje.

ApuGuard AI
Plataforma de seguridad automatizada
""".strip()

    if settings.email_mode.lower() == "console":
        print(
            "\n" + "=" * 72
            + "\nAPUGUARD AI - RECUPERACIÓN DE CONTRASEÑA"
            + f"\nDestinatario: {recipient_email}"
            + f"\nEnlace: {reset_url}"
            + "\n" + "=" * 72,
            flush=True,
        )
        return
    
    if not settings.smtp_user or not settings.smtp_password:
        raise RuntimeError(
            "Las credenciales SMTP no están configuradas."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_user}>"
    )
    message["To"] = recipient_email
    message.set_content(body)

    with smtplib.SMTP(
        settings.smtp_host,
        settings.smtp_port,
        timeout=30,
    ) as smtp:
        smtp.starttls()
        smtp.login(
            settings.smtp_user,
            settings.smtp_password,
        )
        smtp.send_message(message)