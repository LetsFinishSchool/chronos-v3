//! `ai.ask`: Anthropic-Messages-API mit den Werkzeugen aus der Operationsbeschreibung. Führt nichts aus.
use crate::core::cost;
use crate::core::ctx::Ctx;
use crate::core::ops::{self, Operation};
use crate::error::{ApiError, ApiResult};
use crate::register;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::time::Duration;
use utoipa::ToSchema;
use uuid::Uuid;

/// Werkzeugdefinitionen (Anthropic-Format) aus den Operationen; gemeinsam für `/api/v1/ai/tools` und `ai.ask`.
pub fn tools() -> Vec<Value> {
    ops::all()
        .into_iter()
        .map(|o| json!({"name": o.tool_name(), "description": o.description, "input_schema": o.descriptor().params_schema}))
        .collect()
}

#[derive(Deserialize, ToSchema)]
pub struct AskParams {
    #[schema(min_length = 1, max_length = 4000)]
    pub prompt: String,
    pub team_id: Option<Uuid>,
}
#[derive(Serialize, ToSchema)]
pub struct ProposedCall {
    pub name: String,
    #[schema(value_type = Object)]
    pub input: Value,
}
#[derive(Serialize, ToSchema)]
pub struct Usage {
    pub input_tokens: i64,
    pub output_tokens: i64,
}
#[derive(Serialize, ToSchema)]
pub struct AskResult {
    pub text: String,
    pub proposed_calls: Vec<ProposedCall>,
    pub usage: Usage,
}

pub struct AiAsk;
impl Operation for AiAsk {
    type Params = AskParams;
    type Result = AskResult;
    const NAME: &'static str = "ai.ask";
    const DESCRIPTION: &'static str = "Fragt die KI mit den Chronos-Werkzeugen; liefert Text und vorgeschlagene Aufrufe, führt sie aber nicht aus.";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<AskResult> {
        let mut system = String::from(
            "Du bist der Assistent von Chronos, einer Terminverwaltung. Nutze die bereitgestellten Werkzeuge, um Wünsche in Operationen zu übersetzen. \
             Die Aufrufe werden nicht von dir ausgeführt, sondern nur vorgeschlagen. Zeitpunkte gibst du in UTC als ISO 8601 mit Z und Sekundengenauigkeit an (z. B. 2026-12-01T17:00:00Z).",
        );
        if let Some(t) = p.team_id {
            system.push_str(&format!(" Das aktuelle Team hat die team_id {t}."));
        }
        // EIGENBAU:BEGIN Anthropic-Messages-Client (kein ausgereiftes offizielles Rust-SDK): ein Aufruf ohne Streaming
        let body = json!({
            "model": ctx.cfg.anthropic_model,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": p.prompt}],
            "tools": tools(),
        });
        let url = format!("{}/v1/messages", ctx.cfg.anthropic_base_url.trim_end_matches('/'));
        let resp = ctx
            .http
            .post(url)
            .header("x-api-key", &ctx.cfg.anthropic_api_key)
            .header("anthropic-version", "2023-06-01")
            .timeout(Duration::from_secs(60))
            .json(&body)
            .send()
            .await
            .map_err(|e| ApiError::provider(format!("KI nicht erreichbar: {e}")))?;
        let status = resp.status();
        let payload: Value = resp.json().await.map_err(|e| ApiError::provider(format!("KI-Antwort unlesbar: {e}")))?;
        if !status.is_success() {
            tracing::warn!(status = status.as_u16(), "KI-Anbieter antwortete mit Fehler");
            return Err(ApiError::provider(format!("KI-Anbieter antwortete mit {status}")));
        }
        // EIGENBAU:END
        let mut text = String::new();
        let mut calls = Vec::new();
        for block in payload["content"].as_array().cloned().unwrap_or_default() {
            match block["type"].as_str() {
                Some("text") => text.push_str(block["text"].as_str().unwrap_or("")),
                Some("tool_use") => {
                    let tool = block["name"].as_str().unwrap_or("");
                    let name = ops::find_by_tool_name(tool).map(|o| o.name.to_string()).unwrap_or_else(|| tool.to_string());
                    calls.push(ProposedCall { name, input: block["input"].clone() });
                }
                _ => {}
            }
        }
        let usage = Usage { input_tokens: payload["usage"]["input_tokens"].as_i64().unwrap_or(0), output_tokens: payload["usage"]["output_tokens"].as_i64().unwrap_or(0) };
        let per_m = |tokens: i64, price: i64| (tokens * price + 999_999) / 1_000_000;
        let amount = per_m(usage.input_tokens, ctx.cfg.price_in) + per_m(usage.output_tokens, ctx.cfg.price_out);
        let mut c = ctx.pool.acquire().await?;
        cost::record(&mut c, &ctx.caller.id, "anthropic", ctx.op_name, &ctx.correlation_id,
            json!({"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}), amount).await?;
        Ok(AskResult { text, proposed_calls: calls, usage })
    }
}
register!(AiAsk);
