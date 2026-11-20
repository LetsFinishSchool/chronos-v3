use crate::auth::{self, Auth};
use crate::config::Config;
use crate::core::ctx::Ctx;
use crate::core::ops;
use crate::error::{ApiError, ApiResult};
use crate::logging::CORRELATION;
use axum::body::Bytes;
use axum::extract::{Path, Query, Request, State};
use axum::http::{header, HeaderMap, HeaderName, HeaderValue, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Extension, Json, Router};
use serde::Deserialize;
use serde_json::{json, Value};
use sqlx::PgPool;
use std::sync::Arc;
use tower_http::services::ServeDir;
use uuid::Uuid;

#[derive(Clone)]
pub struct AppState {
    pub pool: PgPool,
    pub cfg: Arc<Config>,
    pub http: reqwest::Client,
    pub auth: Arc<Auth>,
}

#[derive(Clone)]
struct Cid(String);

pub fn router(state: AppState) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .route("/api/v1/operations", get(list_operations))
        .route("/api/v1/operations/{name}", post(call_operation))
        .route("/api/v1/ai/tools", get(ai_tools))
        .route("/auth/login", get(login))
        .route("/auth/callback", get(callback))
        .route("/auth/me", get(me))
        .route("/auth/logout", post(logout))
        .nest_service("/static", ServeDir::new(state.cfg.static_dir.clone()))
        .fallback(|| async { ApiError::not_found("Pfad nicht gefunden") })
        .layer(middleware::from_fn(correlation))
        .with_state(state)
}

/// Korrelations-ID übernehmen (≤ 64 Zeichen) oder erzeugen, in Antwort und Logzeilen spiegeln.
async fn correlation(mut req: Request, next: Next) -> Response {
    let cid = req
        .headers()
        .get("x-correlation-id")
        .and_then(|v| v.to_str().ok())
        .filter(|s| !s.is_empty() && s.len() <= 64)
        .map(String::from)
        .unwrap_or_else(|| Uuid::new_v4().to_string());
    req.extensions_mut().insert(Cid(cid.clone()));
    let (method, path) = (req.method().to_string(), req.uri().path().to_string());
    let mut resp = CORRELATION
        .scope(cid.clone(), async {
            let r = next.run(req).await;
            tracing::info!(method = method.as_str(), path = path.as_str(), status = r.status().as_u16(), "Anfrage");
            r
        })
        .await;
    if let Ok(v) = HeaderValue::from_str(&cid) {
        resp.headers_mut().insert(HeaderName::from_static("x-correlation-id"), v);
    }
    resp
}

async fn healthz(State(s): State<AppState>) -> Response {
    match sqlx::query("SELECT 1").execute(&s.pool).await {
        Ok(_) => Json(json!({"status": "ok"})).into_response(),
        Err(_) => (StatusCode::SERVICE_UNAVAILABLE, Json(json!({"status": "db_unreachable"}))).into_response(),
    }
}

async fn list_operations() -> Json<Value> {
    let list: Vec<Value> = ops::all()
        .into_iter()
        .map(|o| {
            let d = o.descriptor();
            json!({"name": o.name, "description": o.description, "mutating": o.mutating, "preview_supported": o.preview_supported,
                   "params_schema": d.params_schema, "result_schema": d.result_schema})
        })
        .collect();
    Json(json!({"operations": list}))
}

async fn ai_tools() -> Json<Value> {
    Json(json!({"tools": crate::ai::tools()}))
}

#[derive(Deserialize)]
struct CallBody {
    #[serde(default = "empty_object")]
    params: Value,
    #[serde(default)]
    preview: bool,
}
fn empty_object() -> Value {
    json!({})
}

async fn call_operation(
    State(s): State<AppState>,
    Extension(Cid(cid)): Extension<Cid>,
    Path(name): Path<String>,
    headers: HeaderMap,
    body: Bytes,
) -> ApiResult<Json<Value>> {
    let person = s.auth.authenticate(&s.pool, &headers).await?;
    let op = ops::find(&name).ok_or_else(|| ApiError::not_found(format!("Operation '{name}' unbekannt")))?;
    let parsed: CallBody = if body.is_empty() {
        CallBody { params: empty_object(), preview: false }
    } else {
        serde_json::from_slice(&body).map_err(|e| ApiError::validation(format!("Ungültiger Anfragekörper: {e}")))?
    };
    let fault = s.cfg.faults && headers.get("x-spike-fault").and_then(|v| v.to_str().ok()) == Some("after_history");
    let ctx = Ctx {
        pool: s.pool.clone(),
        cfg: s.cfg.clone(),
        http: s.http.clone(),
        caller: person,
        correlation_id: cid,
        op_name: op.name,
        fault_after_history: fault,
    };
    let out = op.invoke(ctx, parsed.params, parsed.preview).await?;
    Ok(Json(out))
}

// ---------------------------------------------------------------- Anmeldung

fn found(location: &str) -> Response {
    (StatusCode::FOUND, [(header::LOCATION, location.to_string())]).into_response()
}

async fn login(State(s): State<AppState>) -> ApiResult<Response> {
    Ok(found(&s.auth.login_url(&s.pool).await?))
}

#[derive(Deserialize)]
struct CallbackQuery {
    code: Option<String>,
    state: Option<String>,
}

async fn callback(State(s): State<AppState>, Query(q): Query<CallbackQuery>) -> ApiResult<Response> {
    let (Some(code), Some(state)) = (q.code, q.state) else {
        return Err(ApiError::bad_request("code und state erforderlich"));
    };
    let token = s.auth.callback(&s.pool, &code, &state).await?;
    let mut resp = found("/");
    resp.headers_mut().insert(header::SET_COOKIE, HeaderValue::from_str(&format!("{}={token}; HttpOnly; SameSite=Lax; Path=/", auth::COOKIE)).expect("Cookie"));
    Ok(resp)
}

async fn me(State(s): State<AppState>, headers: HeaderMap) -> ApiResult<Json<Value>> {
    let p = s.auth.authenticate(&s.pool, &headers).await?;
    Ok(Json(json!({"person_id": p.id, "name": p.name, "email": p.email})))
}

async fn logout(State(s): State<AppState>, headers: HeaderMap) -> ApiResult<Response> {
    s.auth.logout(&s.pool, &headers).await?;
    let mut resp = StatusCode::NO_CONTENT.into_response();
    resp.headers_mut().insert(header::SET_COOKIE, HeaderValue::from_str(&format!("{}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0", auth::COOKIE)).expect("Cookie"));
    Ok(resp)
}
