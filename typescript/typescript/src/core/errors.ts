export type ErrorCode =
  | "unauthenticated" | "forbidden" | "not_found" | "validation_error" | "invalid_rrule"
  | "conflict" | "not_undoable" | "provider_error" | "internal";

const STATUS: Record<ErrorCode, number> = {
  unauthenticated: 401, forbidden: 403, not_found: 404, validation_error: 422, invalid_rrule: 422,
  conflict: 409, not_undoable: 409, provider_error: 502, internal: 500,
};

export class AppError extends Error {
  readonly status: number;
  constructor(readonly code: ErrorCode, message: string) {
    super(message);
    this.status = STATUS[code];
  }
}
