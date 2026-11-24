use std::env;

#[derive(Clone, Debug)]
pub struct Config {
    pub database_url: String,
    pub port: u16,
    pub worker_health_port: u16,
    pub oidc_issuer_url: String,
    pub oidc_client_id: String,
    pub oidc_client_secret: String,
    pub oidc_redirect_url: String,
    pub smtp_host: String,
    pub smtp_port: u16,
    pub vapid_private_key: String,
    pub vapid_subject: String,
    pub mock_channel_url: String,
    pub anthropic_base_url: String,
    pub anthropic_api_key: String,
    pub anthropic_model: String,
    pub price_in: i64,
    pub price_out: i64,
    pub email_price: i64,
    pub retry_base_ms: u64,
    pub static_dir: String,
    pub faults: bool,
    pub worker_concurrency: usize,
}

fn var(k: &str, d: &str) -> String {
    env::var(k).unwrap_or_else(|_| d.to_string())
}
fn num<T: std::str::FromStr>(k: &str, d: T) -> T {
    env::var(k).ok().and_then(|v| v.parse().ok()).unwrap_or(d)
}

impl Config {
    pub fn from_env() -> Config {
        Config {
            database_url: var("DATABASE_URL", "postgres://chronos:chronos@localhost:5432/chronos"),
            port: num("PORT", 8080),
            worker_health_port: num("WORKER_HEALTH_PORT", 8081),
            oidc_issuer_url: var("OIDC_ISSUER_URL", ""),
            oidc_client_id: var("OIDC_CLIENT_ID", ""),
            oidc_client_secret: var("OIDC_CLIENT_SECRET", ""),
            oidc_redirect_url: var("OIDC_REDIRECT_URL", ""),
            smtp_host: var("SMTP_HOST", "localhost"),
            smtp_port: num("SMTP_PORT", 1025),
            vapid_private_key: var("VAPID_PRIVATE_KEY", ""),
            vapid_subject: var("VAPID_SUBJECT", "mailto:spike@example.test"),
            mock_channel_url: var("MOCK_CHANNEL_URL", "http://localhost:8090"),
            anthropic_base_url: var("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            anthropic_api_key: var("ANTHROPIC_API_KEY", ""),
            anthropic_model: var("ANTHROPIC_MODEL", "claude-haiku-5-5"),
            price_in: num("AI_PRICE_IN_MICRO_EUR_PER_MTOK", 0),
            price_out: num("AI_PRICE_OUT_MICRO_EUR_PER_MTOK", 0),
            email_price: num("EMAIL_PRICE_MICRO_EUR", 0),
            retry_base_ms: num("RETRY_BASE_MS", 1000),
            static_dir: var("STATIC_DIR", "/static"),
            faults: var("SPIKE_FAULTS", "") == "1",
            worker_concurrency: num("WORKER_CONCURRENCY", 4),
        }
    }
}
