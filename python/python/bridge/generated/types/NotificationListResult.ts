export interface NotificationListResult {
  deliveries: {
    event_id: string;
    event_type: string;
    correlation_id: string;
    trigger: {
      kind: string;
      actor: string;
      [k: string]: unknown;
    };
    recipient: string;
    channel: string;
    attempt: number;
    result: string;
    error: string | null;
    at: string;
    idempotency_key: string;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
