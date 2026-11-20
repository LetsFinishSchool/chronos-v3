use super::{Delivery, Env, Outcome};
use lettre::message::header::{Header, HeaderName, HeaderValue};
use lettre::message::Mailbox;
use lettre::{AsyncSmtpTransport, AsyncTransport, Message, Tokio1Executor};
use std::time::Duration;

macro_rules! text_header {
    ($t:ident, $name:expr) => {
        #[derive(Clone)]
        struct $t(String);
        impl Header for $t {
            fn name() -> HeaderName {
                HeaderName::new_from_ascii_str($name)
            }
            fn parse(s: &str) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
                Ok($t(s.to_string()))
            }
            fn display(&self) -> HeaderValue {
                HeaderValue::new(Self::name(), self.0.clone())
            }
        }
    };
}
text_header!(IdempotencyKey, "X-Chronos-Idempotency-Key");
text_header!(CorrelationId, "X-Chronos-Correlation-Id");

pub async fn send(env: &Env, d: &Delivery) -> Outcome {
    if d.recipient_email.is_empty() {
        return Outcome::Skipped("keine E-Mail-Adresse".into());
    }
    let to: Mailbox = match d.recipient_email.parse() {
        Ok(m) => m,
        Err(e) => return Outcome::Skipped(format!("ungültige E-Mail-Adresse: {e}")),
    };
    let from: Mailbox = "chronos-spike@example.test".parse().expect("feste Absenderadresse");
    let msg = match Message::builder()
        .from(from)
        .to(to)
        .subject(format!("Chronos: {}", d.event_type))
        .header(IdempotencyKey(d.idempotency_key.clone()))
        .header(CorrelationId(d.correlation_id.clone()))
        .body(format!("Ereignis {} ({})", d.event_type, d.event_id))
    {
        Ok(m) => m,
        Err(e) => return Outcome::Failed(format!("Nachricht nicht baubar: {e}")),
    };
    let transport = AsyncSmtpTransport::<Tokio1Executor>::builder_dangerous(env.cfg.smtp_host.clone())
        .port(env.cfg.smtp_port)
        .timeout(Some(Duration::from_secs(10)))
        .build();
    match transport.send(msg).await {
        Ok(_) => Outcome::Success,
        Err(e) => Outcome::Failed(format!("SMTP: {e}")),
    }
}
