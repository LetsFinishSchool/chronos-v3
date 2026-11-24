use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use serde_json::json;

/// Fehler nach V-1 §3: `{"error":{"code":"…","message":"…"}}`.
#[derive(Debug, Clone)]
pub struct ApiError {
    pub status: StatusCode,
    pub code: &'static str,
    pub message: String,
}

impl ApiError {
    fn new(status: StatusCode, code: &'static str, message: impl Into<String>) -> Self {
        ApiError { status, code, message: message.into() }
    }
    pub fn unauthenticated(m: impl Into<String>) -> Self { Self::new(StatusCode::UNAUTHORIZED, "unauthenticated", m) }
    pub fn forbidden(m: impl Into<String>) -> Self { Self::new(StatusCode::FORBIDDEN, "forbidden", m) }
    pub fn not_found(m: impl Into<String>) -> Self { Self::new(StatusCode::NOT_FOUND, "not_found", m) }
    pub fn validation(m: impl Into<String>) -> Self { Self::new(StatusCode::UNPROCESSABLE_ENTITY, "validation_error", m) }
    pub fn invalid_rrule(m: impl Into<String>) -> Self { Self::new(StatusCode::UNPROCESSABLE_ENTITY, "invalid_rrule", m) }
    pub fn conflict(m: impl Into<String>) -> Self { Self::new(StatusCode::CONFLICT, "conflict", m) }
    pub fn not_undoable(m: impl Into<String>) -> Self { Self::new(StatusCode::CONFLICT, "not_undoable", m) }
    pub fn provider(m: impl Into<String>) -> Self { Self::new(StatusCode::BAD_GATEWAY, "provider_error", m) }
    pub fn internal(m: impl Into<String>) -> Self { Self::new(StatusCode::INTERNAL_SERVER_ERROR, "internal", m) }
    pub fn bad_request(m: impl Into<String>) -> Self { Self::new(StatusCode::BAD_REQUEST, "validation_error", m) }
}

impl From<sqlx::Error> for ApiError {
    fn from(e: sqlx::Error) -> Self {
        tracing::error!(error = %e, "Datenbankfehler");
        ApiError::internal("Datenbankfehler")
    }
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        (self.status, axum::Json(json!({"error": {"code": self.code, "message": self.message}}))).into_response()
    }
}

pub type ApiResult<T> = Result<T, ApiError>;

pub type BoxResult<T = ()> = Result<T, Box<dyn std::error::Error + Send + Sync>>;
