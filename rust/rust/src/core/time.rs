use chrono::{DateTime, SecondsFormat, Utc};
use serde::{Deserialize, Deserializer};

pub fn fmt(t: DateTime<Utc>) -> String {
    t.to_rfc3339_opts(SecondsFormat::Secs, true)
}

/// Zeitpunkt in Parametern: ISO 8601 mit Zeitzone, wird nach UTC umgerechnet.
#[derive(Debug, Clone, Copy)]
pub struct Ts(pub DateTime<Utc>);

impl<'de> Deserialize<'de> for Ts {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        let s = String::deserialize(d)?;
        DateTime::parse_from_rfc3339(&s)
            .map(|t| Ts(t.with_timezone(&Utc)))
            .map_err(|e| serde::de::Error::custom(format!("ungültiger Zeitpunkt '{s}': {e}")))
    }
}
