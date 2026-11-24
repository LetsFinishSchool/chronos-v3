export interface SeriesCreateParams {
  team_id: string;
  title: string;
  /**
   * RFC-5545-Regel ohne Präfix RRULE:, z. B. FREQ=WEEKLY;BYDAY=MO
   */
  rrule: string;
  /**
   * Beginn als Ortszeit, z. B. 2026-03-02T18:00:00
   */
  dtstart: string;
  timezone: string;
  duration_minutes: number;
  /**
   * Ausgenommene Vorkommen (Ortszeiten)
   */
  exdates?: string[];
}
