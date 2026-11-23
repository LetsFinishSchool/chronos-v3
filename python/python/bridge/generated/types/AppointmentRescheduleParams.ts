export interface AppointmentRescheduleParams {
  appointment_id: string;
  /**
   * UTC, ISO 8601 mit Z
   */
  starts_at: string;
  /**
   * UTC, ISO 8601 mit Z
   */
  ends_at: string;
}
