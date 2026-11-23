export interface AppointmentGetResult {
  appointment: {
    id: string;
    team_id: string;
    title: string;
    starts_at: string;
    ends_at: string;
    timezone: string;
    status: string;
    [k: string]: unknown;
  };
  [k: string]: unknown;
}
