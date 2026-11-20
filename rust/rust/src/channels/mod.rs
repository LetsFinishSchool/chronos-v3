//! Kanäle: mock, email, webpush. Wird nur vom Worker und von den Benachrichtigungseinstellungen benutzt;
//! die Fachbereiche (`crate::domain`) dürfen dieses Modul nicht kennen (S-9).
pub mod email;
pub mod mock;
pub mod webpush;

use crate::config::Config;
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use utoipa::ToSchema;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, ToSchema)]
#[serde(rename_all = "lowercase")]
pub enum ChannelKind {
    Mock,
    Email,
    Webpush,
}

impl ChannelKind {
    pub fn as_str(&self) -> &'static str {
        match self {
            ChannelKind::Mock => "mock",
            ChannelKind::Email => "email",
            ChannelKind::Webpush => "webpush",
        }
    }
    pub fn parse(s: &str) -> Option<ChannelKind> {
        match s {
            "mock" => Some(ChannelKind::Mock),
            "email" => Some(ChannelKind::Email),
            "webpush" => Some(ChannelKind::Webpush),
            _ => None,
        }
    }
}

/// Ergebnis eines Zustellversuchs.
pub enum Outcome {
    Success,
    Failed(String),
    /// Voraussetzung des Kanals fehlt (z. B. kein Push-Abo, keine E-Mail-Adresse).
    Skipped(String),
}

pub struct Delivery {
    pub event_id: uuid::Uuid,
    pub event_type: String,
    pub correlation_id: String,
    pub recipient: String,
    pub recipient_email: String,
    pub idempotency_key: String,
}

#[derive(Clone)]
pub struct Env {
    pub cfg: std::sync::Arc<Config>,
    pub http: reqwest::Client,
    pub pool: PgPool,
}

pub async fn deliver(kind: ChannelKind, env: &Env, d: &Delivery) -> Outcome {
    match kind {
        ChannelKind::Mock => mock::send(env, d).await,
        ChannelKind::Email => email::send(env, d).await,
        ChannelKind::Webpush => webpush::send(env, d).await,
    }
}
