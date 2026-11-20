use crate::config::Config;
use crate::error::{ApiError, ApiResult};
use sqlx::PgPool;
use std::sync::Arc;

#[derive(Debug, Clone, sqlx::FromRow)]
pub struct Person {
    pub id: String,
    pub name: String,
    pub email: String,
}

/// Aufrufkontext einer Operation.
#[derive(Clone)]
pub struct Ctx {
    pub pool: PgPool,
    pub cfg: Arc<Config>,
    pub http: reqwest::Client,
    pub caller: Person,
    pub correlation_id: String,
    pub op_name: &'static str,
    /// Fehlerinjektion `after_history` angefordert und `SPIKE_FAULTS=1`.
    pub fault_after_history: bool,
}

impl Ctx {
    pub async fn begin(&self) -> ApiResult<sqlx::Transaction<'static, sqlx::Postgres>> {
        self.pool.begin().await.map_err(ApiError::from)
    }
}
