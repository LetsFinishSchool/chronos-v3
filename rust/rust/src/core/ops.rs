//! Operationsrahmen (S-1): Jede Operation wird EINMAL beschrieben (Trait `Operation` + `register!`).
//! Daraus entstehen Validierung (JSON-Schema), Endpunkt, `/api/v1/operations`, KI-Werkzeuge und Brückentypen.
use super::ctx::Ctx;
use crate::error::{ApiError, ApiResult};
use futures::future::BoxFuture;
use jsonschema::Validator;
use serde::de::DeserializeOwned;
use serde::Serialize;
use serde_json::{json, Map, Value};
use std::collections::HashMap;
use std::future::Future;
use std::sync::OnceLock;
use utoipa::ToSchema;

#[derive(Debug, Serialize, ToSchema)]
pub struct Affected {
    #[serde(rename = "type")]
    #[schema(rename = "type")]
    pub kind: String,
    pub id: String,
    pub change: String,
}

#[derive(Debug, Serialize)]
pub struct Preview {
    pub count: usize,
    pub affected: Vec<Affected>,
}

impl Preview {
    pub fn new(affected: Vec<Affected>) -> Self {
        Preview { count: affected.len(), affected }
    }
}

/// Beschreibung einer Operation. Alles Weitere wird daraus abgeleitet.
pub trait Operation: Sized + 'static {
    type Params: DeserializeOwned + ToSchema + Send + 'static;
    type Result: Serialize + ToSchema + Send + 'static;
    const NAME: &'static str;
    const DESCRIPTION: &'static str;
    const MUTATING: bool;
    const PREVIEW: bool = false;

    fn run(ctx: Ctx, params: Self::Params) -> impl Future<Output = ApiResult<Self::Result>> + Send;

    /// Vorschau ohne jede Schreibwirkung; nur für `PREVIEW = true`.
    fn preview(_ctx: Ctx, _params: Self::Params) -> impl Future<Output = ApiResult<Preview>> + Send {
        async { Err(ApiError::validation("Vorschau wird von dieser Operation nicht unterstützt")) }
    }
}

pub struct Descriptor {
    pub params_schema: Value,
    pub result_schema: Value,
    validator: Validator,
}

pub struct OpEntry {
    pub name: &'static str,
    pub description: &'static str,
    pub mutating: bool,
    pub preview_supported: bool,
    schemas: fn() -> (Value, Value),
    call: fn(Ctx, Value, bool) -> BoxFuture<'static, ApiResult<Value>>,
}

inventory::collect!(OpEntry);

/// Registriert eine Operation (einzige Stelle neben der Trait-Implementierung).
#[macro_export]
macro_rules! register {
    ($t:ty) => {
        inventory::submit! { $crate::core::ops::OpEntry::of::<$t>() }
    };
}

impl OpEntry {
    pub const fn of<T: Operation>() -> OpEntry {
        OpEntry {
            name: T::NAME,
            description: T::DESCRIPTION,
            mutating: T::MUTATING,
            preview_supported: T::PREVIEW,
            schemas: schemas_of::<T>,
            call: call_of::<T>,
        }
    }

    pub fn descriptor(&self) -> &'static Descriptor {
        static CACHE: OnceLock<HashMap<&'static str, Descriptor>> = OnceLock::new();
        let map = CACHE.get_or_init(|| {
            inventory::iter::<OpEntry>
                .into_iter()
                .map(|o| {
                    let (params_schema, result_schema) = (o.schemas)();
                    let validator = jsonschema::validator_for(&params_schema).unwrap_or_else(|e| panic!("Schema von {} ungültig: {e}", o.name));
                    (o.name, Descriptor { params_schema, result_schema, validator })
                })
                .collect()
        });
        &map[self.name]
    }

    pub fn tool_name(&self) -> String {
        self.name.replace('.', "_")
    }

    /// Validiert gegen `params_schema`, ruft die Operation auf. Gibt `{"result":…}` oder `{"preview":…}` zurück.
    pub async fn invoke(&self, ctx: Ctx, params: Value, preview: bool) -> ApiResult<Value> {
        let d = self.descriptor();
        let errors: Vec<String> = d.validator.iter_errors(&params).map(|e| format!("{e} ({})", e.instance_path())).collect();
        if !errors.is_empty() {
            return Err(ApiError::validation(errors.join("; ")));
        }
        (self.call)(ctx, params, preview).await
    }
}

pub fn all() -> Vec<&'static OpEntry> {
    let mut v: Vec<&OpEntry> = inventory::iter::<OpEntry>.into_iter().collect();
    v.sort_by_key(|o| o.name);
    v
}

pub fn find(name: &str) -> Option<&'static OpEntry> {
    inventory::iter::<OpEntry>.into_iter().find(|o| o.name == name)
}

pub fn find_by_tool_name(tool: &str) -> Option<&'static OpEntry> {
    inventory::iter::<OpEntry>.into_iter().find(|o| o.tool_name() == tool)
}

fn call_of<T: Operation>(ctx: Ctx, params: Value, preview: bool) -> BoxFuture<'static, ApiResult<Value>> {
    Box::pin(async move {
        let p: T::Params = serde_json::from_value(params).map_err(|e| ApiError::validation(e.to_string()))?;
        if preview && T::MUTATING {
            if !T::PREVIEW {
                return Err(ApiError::validation("Vorschau wird von dieser Operation nicht unterstützt"));
            }
            let pv = T::preview(ctx, p).await?;
            return Ok(json!({"preview": pv}));
        }
        let r = T::run(ctx, p).await?;
        Ok(json!({"result": r}))
    })
}

fn schemas_of<T: Operation>() -> (Value, Value) {
    (schema_json::<T::Params>(true), schema_json::<T::Result>(false))
}

// ---------------------------------------------------------------- Schema-Erzeugung aus utoipa

fn schema_json<T: ToSchema>(params: bool) -> Value {
    let mut defs: Vec<(String, utoipa::openapi::RefOr<utoipa::openapi::schema::Schema>)> = Vec::new();
    T::schemas(&mut defs);
    let defs: HashMap<String, Value> =
        defs.into_iter().map(|(n, s)| (n, serde_json::to_value(s).unwrap_or(Value::Null))).collect();
    let mut root = serde_json::to_value(T::schema()).unwrap_or(Value::Null);
    normalize(&mut root, &defs, params, 0);
    if let Some(o) = root.as_object_mut() {
        o.entry("type").or_insert(json!("object"));
        o.entry("properties").or_insert(json!({}));
        o.entry("required").or_insert(json!([]));
    }
    root
}

/// Löst `$ref` auf, entfernt in Parametern `null`-Varianten (optional = Schlüssel fehlt) und sperrt unbekannte Felder.
fn normalize(v: &mut Value, defs: &HashMap<String, Value>, params: bool, depth: usize) {
    if depth > 16 {
        return;
    }
    if let Some(r) = v.get("$ref").and_then(Value::as_str) {
        let name = r.rsplit('/').next().unwrap_or("");
        if let Some(d) = defs.get(name) {
            *v = d.clone();
        }
    }
    // oneOf/anyOf [null, X] -> X
    for key in ["oneOf", "anyOf"] {
        if let Some(arr) = v.get(key).and_then(Value::as_array) {
            let rest: Vec<Value> = arr.iter().filter(|e| e.get("type") != Some(&json!("null"))).cloned().collect();
            if rest.len() == 1 && (params || rest.len() != arr.len()) {
                let mut inner = rest.into_iter().next().unwrap_or(Value::Null);
                if !params {
                    // Ergebnis: Nullbarkeit beibehalten
                    inner = json!({"oneOf": [{"type": "null"}, inner]});
                    *v = inner;
                    return normalize_children(v, defs, params, depth);
                }
                *v = inner;
                return normalize(v, defs, params, depth + 1);
            }
        }
    }
    if params {
        if let Some(t) = v.get("type").and_then(Value::as_array) {
            let rest: Vec<Value> = t.iter().filter(|e| *e != "null").cloned().collect();
            let new = if rest.len() == 1 { rest[0].clone() } else { Value::Array(rest) };
            v["type"] = new;
        }
    }
    normalize_children(v, defs, params, depth);
}

fn normalize_children(v: &mut Value, defs: &HashMap<String, Value>, params: bool, depth: usize) {
    let is_object = v.get("type").map(|t| t == "object" || t.as_array().is_some_and(|a| a.contains(&json!("object")))).unwrap_or(false)
        || v.get("properties").is_some();
    if let Some(o) = v.as_object_mut() {
        if is_object {
            o.entry("properties").or_insert(Value::Object(Map::new()));
            o.entry("required").or_insert(json!([]));
            if params {
                o.insert("additionalProperties".into(), json!(false));
            }
        }
        for k in ["properties"] {
            if let Some(Value::Object(m)) = o.get_mut(k) {
                for (_, c) in m.iter_mut() {
                    normalize(c, defs, params, depth + 1);
                }
            }
        }
        for k in ["items", "additionalProperties"] {
            if let Some(c) = o.get_mut(k) {
                if c.is_object() {
                    normalize(c, defs, params, depth + 1);
                }
            }
        }
        for k in ["oneOf", "anyOf", "allOf"] {
            if let Some(Value::Array(a)) = o.get_mut(k) {
                for c in a.iter_mut() {
                    normalize(c, defs, params, depth + 1);
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_operation_is_described_once_and_consistently() {
        let all = all();
        assert!(all.len() >= 18, "erwartet mindestens 18 Operationen, gefunden {}", all.len());
        let mut names: Vec<&str> = all.iter().map(|o| o.name).collect();
        names.dedup();
        assert_eq!(names.len(), all.len(), "doppelte Operationsnamen");
        for o in all {
            let d = o.descriptor();
            assert_eq!(d.params_schema["type"], "object", "{}", o.name);
            assert_eq!(d.params_schema["additionalProperties"], false, "{}", o.name);
            assert_eq!(d.result_schema["type"], "object", "{}", o.name);
            assert!(!o.description.is_empty(), "{}", o.name);
        }
    }

    #[test]
    fn ai_tools_follow_operations() {
        let tools = crate::ai::tools();
        assert_eq!(tools.len(), all().len());
        for t in tools {
            let name = t["name"].as_str().unwrap();
            let op = find_by_tool_name(name).expect("Werkzeug ohne Operation");
            assert_eq!(t["input_schema"], op.descriptor().params_schema);
        }
    }

    #[test]
    fn validation_rejects_unknown_and_missing_fields() {
        let d = find("team.create").unwrap().descriptor();
        assert!(d.validator.is_valid(&json!({"name": "x"})));
        assert!(!d.validator.is_valid(&json!({})));
        assert!(!d.validator.is_valid(&json!({"name": "x", "extra": 1})));
        assert!(!d.validator.is_valid(&json!({"name": ""})));
    }
}
