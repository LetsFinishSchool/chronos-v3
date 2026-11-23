export interface AppointmentListResult {
  appointments: {
    id: string;
    team_id: string;
    title: string;
    starts_at: string;
    ends_at: string;
    timezone: string;
    status: string;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
