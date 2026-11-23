export interface TeamEffectiveTeamsResult {
  teams: {
    team_id: string;
    name: string;
    parent_id: string | null;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
