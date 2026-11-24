use serde_json::{Map, Value};
use std::io::Write;
use tracing::field::{Field, Visit};
use tracing::{Event, Subscriber};
use tracing_subscriber::layer::{Context, SubscriberExt};
use tracing_subscriber::util::SubscriberInitExt;
use tracing_subscriber::Layer;

tokio::task_local! {
    /// Korrelations-ID der laufenden Anfrage bzw. Zustellung; wird in jede Logzeile übernommen.
    pub static CORRELATION: String;
}

// EIGENBAU:BEGIN Logformat nach V-1 §3 (Felder ts, level, msg, correlation_id); tracing-subscriber liefert die Feldnamen nicht so.
struct JsonLines;

struct Collect(Map<String, Value>);
impl Visit for Collect {
    fn record_str(&mut self, f: &Field, v: &str) { self.0.insert(f.name().into(), Value::String(v.into())); }
    fn record_i64(&mut self, f: &Field, v: i64) { self.0.insert(f.name().into(), v.into()); }
    fn record_u64(&mut self, f: &Field, v: u64) { self.0.insert(f.name().into(), v.into()); }
    fn record_bool(&mut self, f: &Field, v: bool) { self.0.insert(f.name().into(), v.into()); }
    fn record_debug(&mut self, f: &Field, v: &dyn std::fmt::Debug) {
        self.0.insert(f.name().into(), Value::String(format!("{v:?}")));
    }
}

impl<S: Subscriber> Layer<S> for JsonLines {
    fn on_event(&self, event: &Event<'_>, _ctx: Context<'_, S>) {
        let mut c = Collect(Map::new());
        event.record(&mut c);
        let mut m = Map::new();
        m.insert("ts".into(), chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string().into());
        m.insert("level".into(), event.metadata().level().as_str().to_lowercase().into());
        let msg = c.0.remove("message").unwrap_or(Value::String(String::new()));
        m.insert("msg".into(), msg);
        if !c.0.contains_key("correlation_id") {
            let cid = CORRELATION.try_with(|c| c.clone()).unwrap_or_else(|_| "system".into());
            m.insert("correlation_id".into(), cid.into());
        }
        m.extend(c.0);
        let mut line = serde_json::to_vec(&Value::Object(m)).unwrap_or_default();
        line.push(b'\n');
        let _ = std::io::stdout().lock().write_all(&line);
    }
}
// EIGENBAU:END

pub fn init() {
    let filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info,sqlx=warn,hyper=warn"));
    tracing_subscriber::registry().with(filter).with(JsonLines).init();
}
