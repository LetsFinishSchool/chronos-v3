//! Web-Prozess: HTTP-Server, Sitzung, Auslieferung der Oberfläche.
//!
//! Zuschnitt und erlaubte Abhängigkeiten: `docs/arc42/05-bausteine/02-crate-zuschnitt.md`.

use std::future::Future;

use axum::{Router, routing::get};
use tokio::net::TcpListener;

// Platzhalter, bis Code die Abhängigkeiten nutzt (`unused_crate_dependencies`).
use chronos_adapters as _;
use chronos_core as _;

/// All routes of the web process.
pub fn router() -> Router {
    Router::new().route("/healthz", get(healthz))
}

/// Liveness only; the schema check happens at startup.
async fn healthz() -> &'static str {
    "ok"
}

/// Serves [`router`] on `listener` until `shutdown` completes, then drains open requests.
pub async fn serve(
    listener: TcpListener,
    shutdown: impl Future<Output = ()> + Send + 'static,
) -> std::io::Result<()> {
    axum::serve(listener, router())
        .with_graceful_shutdown(shutdown)
        .await
}

#[cfg(test)]
mod tests {
    use axum::{
        body::{Body, to_bytes},
        http::{Request, StatusCode},
    };
    use tokio::{
        io::{AsyncReadExt, AsyncWriteExt},
        net::{TcpListener, TcpStream},
        sync::oneshot,
    };
    use tower::ServiceExt;

    use super::{router, serve};

    async fn get(path: &str) -> (StatusCode, Vec<u8>) {
        let response = router()
            .oneshot(Request::get(path).body(Body::empty()).unwrap())
            .await
            .unwrap();
        let status = response.status();
        let body = to_bytes(response.into_body(), usize::MAX).await.unwrap();
        (status, body.to_vec())
    }

    #[tokio::test]
    async fn healthz_returns_ok() {
        let (status, body) = get("/healthz").await;
        assert_eq!(status, StatusCode::OK);
        assert_eq!(body, b"ok");
    }

    #[tokio::test]
    async fn unknown_route_returns_404() {
        let (status, _) = get("/does-not-exist").await;
        assert_eq!(status, StatusCode::NOT_FOUND);
    }

    #[tokio::test]
    async fn serve_answers_over_tcp_and_stops_on_shutdown() {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let (stop, stopped) = oneshot::channel::<()>();
        let server = tokio::spawn(serve(listener, async {
            let _ = stopped.await;
        }));

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
