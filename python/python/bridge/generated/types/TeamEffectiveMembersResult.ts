export interface TeamEffectiveMembersResult {
  members: {
    person_id: string;
    name: string;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
