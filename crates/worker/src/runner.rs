//! Pacing of the processing: polling instead of `LISTEN/NOTIFY`, orderly shutdown (#102).

use std::num::NonZeroU32;
use std::time::Duration;

use chronos_core::{ConsumerRegistry, Outbox};
use tokio::time::sleep;
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

const DEFAULT_POLL_INTERVAL: Duration = Duration::from_secs(2);
const DEFAULT_BATCH_SIZE: NonZeroU32 = NonZeroU32::new(50).unwrap();

#[derive(Clone, Copy, Debug)]
pub struct WorkerConfig {
    /// Pause when a batch was not full.
    pub poll_interval: Duration,
    pub batch_size: NonZeroU32,
}

impl Default for WorkerConfig {
    fn default() -> Self {
        Self {
            poll_interval: DEFAULT_POLL_INTERVAL,
            batch_size: DEFAULT_BATCH_SIZE,
        }
    }
}

/// Works through the outbox until `shutdown` is triggered. A running batch is still
/// finished, then the function returns.
///
/// A full batch triggers the next one immediately, otherwise the loop waits
/// `poll_interval`. Failed events are therefore retried on every run; a limit and a delay
/// for that are deliberately left open (#23).
pub async fn run(
    outbox: &Outbox,
    registry: &ConsumerRegistry,
    config: &WorkerConfig,
    shutdown: CancellationToken,
) {
    info!(
        poll_interval_ms = config.poll_interval.as_millis() as u64,
        batch_size = config.batch_size.get(),
        "worker started",
    );
    while !shutdown.is_cancelled() {
        match outbox
            .process_batch(registry, config.batch_size.get())
            .await
        {
            Ok(stats) if stats.processed >= config.batch_size.get() => continue,
            Ok(_) => {}
            Err(source) => error!(error = %source, "outbox batch failed"),
        }
        tokio::select! {
            () = shutdown.cancelled() => {}
            () = sleep(config.poll_interval) => {}
        }
    }
    info!("worker stopped");
}
