//! Web-Prozess: HTTP-Server, Sitzung, Auslieferung der Oberfläche.
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use std::future::Future;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use axum::{
    Router,
    extract::{Request, State},
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{any, get},
};
use tokio::net::TcpListener;
use tower_http::services::{ServeDir, ServeFile};

// Platzhalter, bis Code die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_core as _;

/// Prefix reserved for the API (#96); it never falls back to the SPA shell.
const API_PREFIX: &str = "/api";

/// All routes of the web process; the built frontend in `frontend_dir` answers everything else.
///
/// Unknown page paths get `index.html` with status 200 so the SPA can render its own "not found"
/// page. Missing assets get a real 404: a stale `index.html` asking for an old hashed script must
/// not receive HTML.
pub fn router(frontend_dir: &Path) -> Router {
    let index = Arc::new(frontend_dir.join(INDEX_FILE));
    let frontend = ServeDir::new(frontend_dir)
        .fallback(axum::routing::any(shell_or_not_found).with_state(index));
    Router::new()
        .route("/healthz", get(healthz))
        .route(API_PREFIX, any(api_not_found))
        .route("/api/", any(api_not_found))
        .route("/api/{*path}", any(api_not_found))
        .fallback_service(frontend)
}

/// Entry file of the SPA build, also used as the fallback document.
pub const INDEX_FILE: &str = "index.html";

/// Asset paths: the build's own directory and anything with a file extension (`/favicon.ico`).
fn is_asset_path(path: &str) -> bool {
    path.starts_with("/_app/")
        || path
            .rsplit('/')
            .next()
            .is_some_and(|name| name.contains('.'))
}

async fn shell_or_not_found(State(index): State<Arc<PathBuf>>, request: Request) -> Response {
    if is_asset_path(request.uri().path()) {
        return StatusCode::NOT_FOUND.into_response();
    }
    match ServeFile::new(index.as_path()).try_call(request).await {
        Ok(response) => response.into_response(),
        Err(_) => StatusCode::INTERNAL_SERVER_ERROR.into_response(),
    }
}

async fn api_not_found() -> StatusCode {
    StatusCode::NOT_FOUND
}

/// Liveness only; the schema check happens at startup.
async fn healthz() -> &'static str {
    "ok"
}

/// Serves [`router`] on `listener` until `shutdown` completes, then drains open requests.
pub async fn serve(
    listener: TcpListener,
    frontend_dir: &Path,
    shutdown: impl Future<Output = ()> + Send + 'static,
) -> std::io::Result<()> {
    axum::serve(listener, router(frontend_dir))
        .with_graceful_shutdown(shutdown)
        .await
}

#[cfg(test)]
mod tests {
    use std::path::{Path, PathBuf};

    use axum::{
        body::{Body, to_bytes},
        http::{Method, Request, StatusCode},
    };
    use tokio::{
        io::{AsyncReadExt, AsyncWriteExt},
        net::{TcpListener, TcpStream},
        sync::oneshot,
    };
    use tower::ServiceExt;

    use super::{INDEX_FILE, router, serve};

    const INDEX_HTML: &str = "<h1>shell</h1>";
    const ASSET: &[u8] = b"console.log('asset');\n";

    /// Build directory with an entry file and one asset, removed on drop.
    struct Frontend(PathBuf);

    impl Frontend {
        fn new(name: &str) -> Self {
            let dir =
                std::env::temp_dir().join(format!("chronos-web-{}-{name}", std::process::id()));
            std::fs::create_dir_all(dir.join("_app")).unwrap();
            std::fs::write(dir.join(INDEX_FILE), INDEX_HTML).unwrap();
            std::fs::write(dir.join("_app/app.js"), ASSET).unwrap();
            Self(dir)
        }

        fn path(&self) -> &Path {
            &self.0
        }
    }

    impl Drop for Frontend {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.0);
        }
    }

    async fn request(frontend: &Frontend, method: Method, path: &str) -> (StatusCode, Vec<u8>) {
        let response = router(frontend.path())
            .oneshot(
                Request::builder()
                    .method(method)
                    .uri(path)
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        let status = response.status();
        let body = to_bytes(response.into_body(), usize::MAX).await.unwrap();
        (status, body.to_vec())
    }

    async fn get(frontend: &Frontend, path: &str) -> (StatusCode, Vec<u8>) {
        request(frontend, Method::GET, path).await
    }

    #[tokio::test]
    async fn healthz_returns_ok() {
        let frontend = Frontend::new("healthz");
        let (status, body) = get(&frontend, "/healthz").await;
        assert_eq!(status, StatusCode::OK);
        assert_eq!(body, b"ok");
    }

    #[tokio::test]
    async fn root_serves_the_entry_page() {
        let frontend = Frontend::new("root");
        let (status, body) = get(&frontend, "/").await;
        assert_eq!(status, StatusCode::OK);
        assert_eq!(body, INDEX_HTML.as_bytes());
    }

    #[tokio::test]
    async fn unknown_path_falls_back_to_the_entry_page_with_200() {
        let frontend = Frontend::new("fallback");
        for method in [Method::GET, Method::HEAD] {
            let (status, body) = request(&frontend, method.clone(), "/irgendwas/tief").await;
            assert_eq!(status, StatusCode::OK, "{method}");
            if method == Method::GET {
                assert_eq!(body, INDEX_HTML.as_bytes());
            }
        }
    }

    #[tokio::test]
    async fn missing_assets_are_404_not_the_shell() {
        let frontend = Frontend::new("missing-asset");
        for path in [
            "/_app/immutable/entry/start.OLD.js",
            "/favicon.ico",
            "/a/b.css",
        ] {
            let (status, body) = get(&frontend, path).await;
            assert_eq!(status, StatusCode::NOT_FOUND, "{path}");
            assert!(!body.starts_with(b"<h1>"), "{path}");
        }
    }

    #[tokio::test]
    async fn existing_file_is_served_unchanged() {
        let frontend = Frontend::new("asset");
        let (status, body) = get(&frontend, "/_app/app.js").await;
        assert_eq!(status, StatusCode::OK);
        assert_eq!(body, ASSET);
    }

    #[tokio::test]
    async fn api_prefix_is_never_answered_by_the_shell() {
        let frontend = Frontend::new("api");
        for path in ["/api", "/api/", "/api/irgendwas", "/api/a/b"] {
            for method in [Method::GET, Method::HEAD, Method::POST] {
                let (status, body) = request(&frontend, method.clone(), path).await;
                assert_eq!(status, StatusCode::NOT_FOUND, "{method} {path}");
                assert!(!body.starts_with(b"<h1>"), "{method} {path}");
            }
        }
    }

    #[tokio::test]
    async fn serve_answers_over_tcp_and_stops_on_shutdown() {
        let frontend = Frontend::new("tcp");
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let (stop, stopped) = oneshot::channel::<()>();
        let dir = frontend.path().to_owned();
        let server = tokio::spawn(async move {
            serve(listener, &dir, async {
                let _ = stopped.await;
            })
            .await
        });

        let mut stream = TcpStream::connect(address).await.unwrap();
        stream
            .write_all(b"GET /healthz HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n")
            .await
            .unwrap();
        let mut response = String::new();
        stream.read_to_string(&mut response).await.unwrap();
        assert!(response.starts_with("HTTP/1.1 200"), "{response}");
        assert!(response.ends_with("ok"), "{response}");

        stop.send(()).unwrap();
        server.await.unwrap().unwrap();
    }
}
