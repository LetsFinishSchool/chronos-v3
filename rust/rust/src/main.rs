mod ai;
mod auth;
mod channels;
mod config;
mod core;
mod db;
mod domain;
mod error;
mod logging;
mod notify;
mod web;
mod worker;

use std::sync::Arc;

#[tokio::main]
async fn main() {
    logging::init();
    let mode = std::env::args().nth(1).unwrap_or_else(|| "web".into());
    let cfg = config::Config::from_env();
    let result = match mode.as_str() {
        "web" => run_web(cfg).await,
        "worker" => worker::run(cfg).await,
        other => Err(format!("Unbekannter Startmodus '{other}' (web oder worker)").into()),
    };
    if let Err(e) = result {
        tracing::error!(error = %e, "Prozess beendet");
        std::process::exit(1);
    }
}

async fn run_web(cfg: config::Config) -> error::BoxResult {
    let cfg = Arc::new(cfg);
    let pool = db::connect(&cfg.database_url).await?;
    db::migrate(&pool).await?;
    let http = reqwest::Client::new();
    let state = web::AppState { pool, cfg: cfg.clone(), http: http.clone(), auth: Arc::new(auth::Auth::new(cfg.clone(), http)) };
    let listener = tokio::net::TcpListener::bind(("0.0.0.0", cfg.port)).await?;
    tracing::info!(port = cfg.port, operations = core::ops::all().len(), "Web gestartet");
    axum::serve(listener, web::router(state)).await?;
    Ok(())
}
