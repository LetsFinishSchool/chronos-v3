"""Kanal email: SMTP (aiosmtplib), ohne TLS und Anmeldung."""
from email.message import EmailMessage

import aiosmtplib

from chronos.channels.base import ChannelError, Message, Skipped
from chronos.config import settings

name = "email"


async def deliver(msg: Message) -> None:
    if not msg.recipient_email:
        raise Skipped("keine E-Mail-Adresse bekannt")
    mail = EmailMessage()
    mail["From"] = "chronos-spike@example.test"
    mail["To"] = msg.recipient_email
    mail["Subject"] = f"Chronos: {msg.event_type}"
    mail["X-Chronos-Idempotency-Key"] = msg.idempotency_key
    mail["X-Chronos-Correlation-Id"] = msg.correlation_id
    mail.set_content(f"Ereignis {msg.event_type} ({msg.event_id}).")
    try:
        await aiosmtplib.send(mail, hostname=settings.smtp_host, port=settings.smtp_port, use_tls=False,
                              start_tls=False, timeout=10)
    except (aiosmtplib.SMTPException, OSError) as e:
        raise ChannelError(f"SMTP: {type(e).__name__}") from e
