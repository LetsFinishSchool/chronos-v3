use super::{Delivery, Env, Outcome};
use serde_json::json;
use std::time::Duration;

pub async fn send(env: &Env, d: &Delivery) -> Outcome {
    let url = format!("{}/deliver", env.cfg.mock_channel_url.trim_end_matches('/'));
    let body = json!({"recipient": d.recipient, "event_type": d.event_type, "event_id": d.event_id, "correlation_id": d.correlation_id});
    match env.http.post(url).header("Idempotency-Key", &d.idempotency_key).timeout(Duration::from_secs(10)).json(&body).send().await {
        Ok(r) if r.status().is_success() => Outcome::Success,
        Ok(r) => Outcome::Failed(format!("Mock-Kanal antwortete {}", r.status())),
        Err(e) => Outcome::Failed(format!("Mock-Kanal nicht erreichbar: {e}")),
    }
}
