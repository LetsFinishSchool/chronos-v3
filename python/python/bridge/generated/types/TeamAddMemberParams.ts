export interface TeamAddMemberParams {
  team_id: string;
  /**
   * Keycloak-sub der Person
   */
  person_id: string;
}
