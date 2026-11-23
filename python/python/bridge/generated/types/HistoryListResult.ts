export interface HistoryListResult {
  entries: {
    id: string;
    at: string;
    actor: string;
    action: string;
    object_type: string;
    object_id: string;
    before: {
      [k: string]: unknown;
    } | null;
    after: {
      [k: string]: unknown;
    } | null;
    bundle_id: string;
    correlation_id: string;
    undone: boolean;
    undo_of: string | null;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
