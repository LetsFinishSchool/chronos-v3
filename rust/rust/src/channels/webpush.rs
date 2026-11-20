use super::{Delivery, Env, Outcome};
use serde_json::json;
use web_push::{ContentEncoding, HyperWebPushClient, SubscriptionInfo, VapidSignatureBuilder, WebPushClient, WebPushMessageBuilder};

pub async fn send(env: &Env, d: &Delivery) -> Outcome {
    let subs: Vec<(String, String, String)> = match sqlx::query_as("SELECT endpoint, p256dh, auth FROM push_subscriptions WHERE person_id = $1")
        .bind(&d.recipient)
        .fetch_all(&env.pool)
        .await
    {
        Ok(s) => s,
        Err(e) => return Outcome::Failed(format!("Datenbank: {e}")),
    };
    if subs.is_empty() {
        return Outcome::Skipped("kein Push-Abonnement".into());
    }
    let payload = json!({"event_type": d.event_type, "event_id": d.event_id}).to_string();
    let client = HyperWebPushClient::new();
    let mut last_err = String::new();
    let mut ok = false;
    for (endpoint, p256dh, auth) in subs {
        let info = SubscriptionInfo::new(endpoint, p256dh, auth);
        let attempt = async {
            let mut sig = VapidSignatureBuilder::from_base64(&env.cfg.vapid_private_key, &info)?;
            sig.add_claim("sub", env.cfg.vapid_subject.as_str());
            let mut b = WebPushMessageBuilder::new(&info);
            b.set_payload(ContentEncoding::Aes128Gcm, payload.as_bytes());
            b.set_vapid_signature(sig.build()?);
            client.send(b.build()?).await
        };
        match attempt.await {
            Ok(()) => ok = true,
            Err(e) => last_err = format!("Web Push: {e}"),
        }
    }
    if ok { Outcome::Success } else { Outcome::Failed(last_err) }
}
