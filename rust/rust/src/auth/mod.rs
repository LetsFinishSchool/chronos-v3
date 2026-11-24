//! Anmeldung (S-6): Bearer-Prüfung über JWKS (jsonwebtoken), OIDC-Code-Flow mit PKCE (openidconnect), Sitzungen in der Datenbank.
use crate::config::Config;
use crate::core::ctx::Person;
use crate::error::{ApiError, ApiResult};
use axum::http::{header, HeaderMap};
use jsonwebtoken::jwk::JwkSet;
use jsonwebtoken::{decode, decode_header, Algorithm, DecodingKey, Validation};
use openidconnect::core::{CoreAuthenticationFlow, CoreClient, CoreProviderMetadata};
use openidconnect::{
    AuthorizationCode, ClientId, ClientSecret, CsrfToken, IssuerUrl, Nonce, PkceCodeChallenge, PkceCodeVerifier, RedirectUrl, Scope,
    TokenResponse,
};
use serde::Deserialize;
use sqlx::PgPool;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{OnceCell, RwLock};

pub const COOKIE: &str = "chronos_session";

#[derive(Deserialize)]
struct Claims {
    sub: String,
    preferred_username: Option<String>,
    email: Option<String>,
}

pub struct Auth {
    cfg: Arc<Config>,
    http: openidconnect::reqwest::Client,
    plain_http: reqwest::Client,
    jwks: RwLock<Option<(Instant, JwkSet)>>,
    metadata: OnceCell<CoreProviderMetadata>,
}

impl Auth {
    pub fn new(cfg: Arc<Config>, plain_http: reqwest::Client) -> Auth {
        let http = openidconnect::reqwest::Client::builder()
            .redirect(openidconnect::reqwest::redirect::Policy::none())
            .build()
            .expect("HTTP-Client für OIDC");
        Auth { cfg, http, plain_http, jwks: RwLock::new(None), metadata: OnceCell::new() }
    }

    // ------------------------------------------------------------ Bearer

    async fn fetch_jwks(&self) -> ApiResult<JwkSet> {
        let url = format!("{}/protocol/openid-connect/certs", self.cfg.oidc_issuer_url.trim_end_matches('/'));
        let set: JwkSet = self
            .plain_http
            .get(url)
            .timeout(Duration::from_secs(10))
            .send()
            .await
            .and_then(|r| r.error_for_status())
            .map_err(|e| ApiError::internal(format!("JWKS nicht abrufbar: {e}")))?
            .json()
            .await
            .map_err(|e| ApiError::internal(format!("JWKS unlesbar: {e}")))?;
        *self.jwks.write().await = Some((Instant::now(), set.clone()));
        Ok(set)
    }

    async fn key_for(&self, kid: &str) -> ApiResult<DecodingKey> {
        let cached = self.jwks.read().await.clone();
        if let Some((at, set)) = &cached {
            if let Some(j) = set.find(kid) {
                if at.elapsed() < Duration::from_secs(600) {
                    return DecodingKey::from_jwk(j).map_err(|_| ApiError::unauthenticated("Schlüssel unbrauchbar"));
                }
            }
        }
        // unbekannte Schlüsselkennung oder veraltet: neu laden (höchstens alle 5 s)
        if let Some((at, _)) = &cached {
            if at.elapsed() < Duration::from_secs(5) {
                return Err(ApiError::unauthenticated("Unbekannter Signaturschlüssel"));
            }
        }
        let set = self.fetch_jwks().await?;
        let j = set.find(kid).ok_or_else(|| ApiError::unauthenticated("Unbekannter Signaturschlüssel"))?;
        DecodingKey::from_jwk(j).map_err(|_| ApiError::unauthenticated("Schlüssel unbrauchbar"))
    }

    async fn verify_bearer(&self, token: &str) -> ApiResult<Claims> {
        let bad = |_| ApiError::unauthenticated("Ungültiges Token");
        let header = decode_header(token).map_err(bad)?;
        let kid = header.kid.ok_or_else(|| ApiError::unauthenticated("Token ohne kid"))?;
        if !matches!(header.alg, Algorithm::RS256 | Algorithm::RS384 | Algorithm::RS512 | Algorithm::ES256 | Algorithm::ES384) {
            return Err(ApiError::unauthenticated("Algorithmus nicht zugelassen"));
        }
        let key = self.key_for(&kid).await?;
        let mut v = Validation::new(header.alg);
        v.set_issuer(&[self.cfg.oidc_issuer_url.as_str()]);
        v.validate_aud = false;
        v.set_required_spec_claims(&["exp", "iss", "sub"]);
        decode::<Claims>(token, &key, &v).map(|d| d.claims).map_err(bad)
    }

    /// Person aus Bearer-Token (wird angelegt/aktualisiert) oder aus dem Sitzungs-Cookie.
    pub async fn authenticate(&self, pool: &PgPool, headers: &HeaderMap) -> ApiResult<Person> {
        if let Some(h) = headers.get(header::AUTHORIZATION) {
            let h = h.to_str().unwrap_or("");
            let token = h.strip_prefix("Bearer ").or_else(|| h.strip_prefix("bearer ")).ok_or_else(|| ApiError::unauthenticated("Bearer-Token erwartet"))?;
            let c = self.verify_bearer(token.trim()).await?;
            return upsert_person(pool, &c.sub, c.preferred_username.as_deref().unwrap_or(&c.sub), c.email.as_deref().unwrap_or("")).await;
        }
        if let Some(tok) = cookie_value(headers, COOKIE) {
            let p: Option<Person> = sqlx::query_as(
                "SELECT p.id, p.name, p.email FROM sessions s JOIN persons p ON p.id = s.person_id WHERE s.token = $1",
            )
            .bind(tok)
            .fetch_optional(pool)
            .await?;
            return p.ok_or_else(|| ApiError::unauthenticated("Sitzung ungültig"));
        }
        Err(ApiError::unauthenticated("Anmeldung erforderlich"))
    }

    // ------------------------------------------------------------ OIDC-Fluss

    async fn client(&self) -> ApiResult<CoreClient<openidconnect::EndpointSet, openidconnect::EndpointNotSet, openidconnect::EndpointNotSet, openidconnect::EndpointNotSet, openidconnect::EndpointMaybeSet, openidconnect::EndpointMaybeSet>> {
        let meta = self
            .metadata
            .get_or_try_init(|| async {
                let issuer = IssuerUrl::new(self.cfg.oidc_issuer_url.clone()).map_err(|e| ApiError::internal(format!("Issuer: {e}")))?;
                CoreProviderMetadata::discover_async(issuer, &self.http).await.map_err(|e| ApiError::internal(format!("OIDC-Discovery: {e}")))
            })
            .await?
            .clone();
        let redirect = RedirectUrl::new(self.cfg.oidc_redirect_url.clone()).map_err(|e| ApiError::internal(format!("Redirect-URL: {e}")))?;
        Ok(CoreClient::from_provider_metadata(meta, ClientId::new(self.cfg.oidc_client_id.clone()), Some(ClientSecret::new(self.cfg.oidc_client_secret.clone())))
            .set_redirect_uri(redirect))
    }

    /// URL des Autorisierungsendpunkts (Code-Flow, PKCE S256, state); Zustand wird in der Datenbank gehalten.
    pub async fn login_url(&self, pool: &PgPool) -> ApiResult<String> {
        let client = self.client().await?;
        let (challenge, verifier) = PkceCodeChallenge::new_random_sha256();
        let (url, state, nonce) = client
            .authorize_url(CoreAuthenticationFlow::AuthorizationCode, CsrfToken::new_random, Nonce::new_random)
            .add_scope(Scope::new("email".into()))
            .add_scope(Scope::new("profile".into()))
            .set_pkce_challenge(challenge)
            .url();
        sqlx::query("DELETE FROM oidc_states WHERE created_at < now() - interval '15 minutes'").execute(pool).await?;
        sqlx::query("INSERT INTO oidc_states (state, pkce_verifier, nonce) VALUES ($1,$2,$3)")
            .bind(state.secret()).bind(verifier.secret()).bind(nonce.secret()).execute(pool).await?;
        Ok(url.to_string())
    }

    /// Tauscht den Code, legt Person und Sitzung an; gibt das Sitzungstoken zurück.
    pub async fn callback(&self, pool: &PgPool, code: &str, state: &str) -> ApiResult<String> {
        let row: Option<(String, String)> = sqlx::query_as("DELETE FROM oidc_states WHERE state = $1 AND created_at > now() - interval '15 minutes' RETURNING pkce_verifier, nonce")
            .bind(state).fetch_optional(pool).await?;
        let (verifier, nonce) = row.ok_or_else(|| ApiError::bad_request("Ungültiger state"))?;
        let client = self.client().await?;
        let tokens = client
            .exchange_code(AuthorizationCode::new(code.to_string()))
            .map_err(|e| ApiError::internal(format!("Token-Endpunkt: {e}")))?
            .set_pkce_verifier(PkceCodeVerifier::new(verifier))
            .request_async(&self.http)
            .await
            .map_err(|e| ApiError::bad_request(format!("Code-Tausch fehlgeschlagen: {e}")))?;
        let id_token = tokens.id_token().ok_or_else(|| ApiError::bad_request("Kein ID-Token erhalten"))?;
        let claims = id_token
            .claims(&client.id_token_verifier(), &Nonce::new(nonce))
            .map_err(|e| ApiError::unauthenticated(format!("ID-Token ungültig: {e}")))?;
        let sub = claims.subject().as_str().to_string();
        let name = claims.preferred_username().map(|u| u.as_str().to_string()).unwrap_or_else(|| sub.clone());
        let email = claims.email().map(|e| e.as_str().to_string()).unwrap_or_default();
        upsert_person(pool, &sub, &name, &email).await?;
        let token = format!("{}{}", Uuid::new_v4().simple(), Uuid::new_v4().simple());
        sqlx::query("INSERT INTO sessions (token, person_id) VALUES ($1,$2)").bind(&token).bind(&sub).execute(pool).await?;
        Ok(token)
    }

    pub async fn logout(&self, pool: &PgPool, headers: &HeaderMap) -> ApiResult<()> {
        if let Some(tok) = cookie_value(headers, COOKIE) {
            sqlx::query("DELETE FROM sessions WHERE token = $1").bind(tok).execute(pool).await?;
        }
        Ok(())
    }
}

use uuid::Uuid;

pub async fn upsert_person(pool: &PgPool, id: &str, name: &str, email: &str) -> ApiResult<Person> {
    let p: Person = sqlx::query_as(
        "INSERT INTO persons (id, name, email) VALUES ($1,$2,$3)
         ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email
         RETURNING id, name, email",
    )
    .bind(id).bind(name).bind(email)
    .fetch_one(pool)
    .await?;
    Ok(p)
}

pub fn cookie_value<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str> {
    headers.get(header::COOKIE)?.to_str().ok()?.split(';').filter_map(|p| p.trim().split_once('=')).find(|(k, _)| *k == name).map(|(_, v)| v)
}
