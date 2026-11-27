//! Schemaquelle der Operationen. Alles Schemarelevante läuft über dieses Modul, damit ein
//! Wechsel von `schemars` zu `utoipa` (E-005a, offen) nur hier und im Rahmen ankommt.

pub use schemars::{self, JsonSchema};

pub fn of<T: JsonSchema>() -> serde_json::Value {
    serde_json::to_value(schemars::schema_for!(T)).expect("a schema can be represented as JSON")
}
