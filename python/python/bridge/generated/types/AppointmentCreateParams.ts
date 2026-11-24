export interface AppointmentCreateParams {
  team_id: string;
  title: string;
  /**
   * UTC, ISO 8601 mit Z
   */
  starts_at: string;
  /**
   * UTC, ISO 8601 mit Z
   */
  ends_at: string;
  /**
   * IANA-Zeitzonenname, z. B. Europe/Berlin
   */
  timezone: string;
}
