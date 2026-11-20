// GENERIERT von scripts/bridge.ts aus /api/v1/operations. Nicht von Hand ändern.

export interface AiAskParams {
prompt: string
/**
 * UUID
 */
team_id?: string
}
export interface AiAskResult {
text: string
proposed_calls: {
name: string
input: {
[k: string]: unknown
}
}[]
usage: {
input_tokens: number
output_tokens: number
}
}
export interface AppointmentCancelParams {
/**
 * UUID
 */
appointment_id: string
}
export interface AppointmentCancelResult {

}
export interface AppointmentCreateParams {
/**
 * UUID
 */
team_id: string
title: string
/**
 * UTC, ISO 8601 mit Z
 */
starts_at: string
/**
 * UTC, ISO 8601 mit Z
 */
ends_at: string
/**
 * IANA-Zeitzone
 */
timezone: string
}
export interface AppointmentCreateResult {
/**
 * UUID
 */
appointment_id: string
}
export interface AppointmentGetParams {
/**
 * UUID
 */
appointment_id: string
}
export interface AppointmentGetResult {
appointment: {
/**
 * UUID
 */
id: string
/**
 * UUID
 */
team_id: string
title: string
/**
 * UTC, ISO 8601 mit Z
 */
starts_at: string
/**
 * UTC, ISO 8601 mit Z
 */
ends_at: string
/**
 * IANA-Zeitzone
 */
timezone: string
status: ("geplant" | "abgesagt" | "gelöscht")
}
}
export interface AppointmentListParams {
/**
 * UUID
 */
team_id: string
}
export interface AppointmentListResult {
appointments: {
/**
 * UUID
 */
id: string
/**
 * UUID
 */
team_id: string
title: string
/**
 * UTC, ISO 8601 mit Z
 */
starts_at: string
/**
 * UTC, ISO 8601 mit Z
 */
ends_at: string
/**
 * IANA-Zeitzone
 */
timezone: string
status: ("geplant" | "abgesagt" | "gelöscht")
}[]
}
export interface AppointmentRescheduleParams {
/**
 * UUID
 */
appointment_id: string
/**
 * UTC, ISO 8601 mit Z
 */
starts_at: string
/**
 * UTC, ISO 8601 mit Z
 */
ends_at: string
}
export interface AppointmentRescheduleResult {

}
export interface CostListParams {
limit?: number
}
export interface CostListResult {
entries: {
id: string
/**
 * UTC, ISO 8601 mit Z
 */
at: string
person_id: string
provider: ("anthropic" | "smtp")
trigger: {
kind: string
name: string
correlation_id: string
}
quantity: {
[k: string]: number
}
amount_micro_eur: number
}[]
}
export interface HistoryListParams {
/**
 * UUID
 */
object_id?: string
limit?: number
}
export interface HistoryListResult {
entries: {
/**
 * UUID
 */
id: string
/**
 * UTC, ISO 8601 mit Z
 */
at: string
actor: string
action: string
object_type: string
/**
 * UUID
 */
object_id: string
before: unknown
after: unknown
/**
 * UUID
 */
bundle_id: string
correlation_id: string
undone: boolean
undo_of: (string | null)
}[]
}
export interface HistoryUndoParams {
/**
 * UUID
 */
history_id: string
}
export interface HistoryUndoResult {
/**
 * UUID
 */
history_id: string
}
export interface NotificationListParams {
/**
 * UUID
 */
event_id?: string
correlation_id?: string
limit?: number
}
export interface NotificationListResult {
deliveries: {
/**
 * UUID
 */
event_id: string
event_type: string
correlation_id: string
trigger: {
kind: string
actor: string
}
recipient: string
channel: ("mock" | "email" | "webpush")
attempt: number
result: ("success" | "failed" | "skipped")
error?: string
/**
 * UTC, ISO 8601 mit Z
 */
at: string
idempotency_key: string
}[]
}
export interface NotificationSetChannelsParams {
/**
 * @minItems 1
 */
channels: [("mock" | "email" | "webpush"), ...(("mock" | "email" | "webpush"))[]]
}
export interface NotificationSetChannelsResult {

}
export interface NotificationSubscribePushParams {
endpoint: string
p256dh: string
auth: string
}
export interface NotificationSubscribePushResult {

}
export interface NotificationTestPushParams {

}
export interface NotificationTestPushResult {
/**
 * UUID
 */
event_id: string
}
export interface SeriesCreateParams {
/**
 * UUID
 */
team_id: string
title: string
rrule: string
/**
 * Ortszeit ohne Zone
 */
dtstart: string
/**
 * IANA-Zeitzone
 */
timezone: string
duration_minutes: number
/**
 * Items: Ortszeit ohne Zone
 */
exdates?: string[]
}
export interface SeriesCreateResult {
/**
 * UUID
 */
series_id: string
}
export interface SeriesOccurrencesParams {
/**
 * UUID
 */
series_id: string
/**
 * UTC, ISO 8601 mit Z
 */
from: string
/**
 * UTC, ISO 8601 mit Z
 */
to: string
}
export interface SeriesOccurrencesResult {
occurrences: {
/**
 * UTC, ISO 8601 mit Z
 */
starts_at: string
/**
 * UTC, ISO 8601 mit Z
 */
ends_at: string
}[]
}
export interface TeamAddMemberParams {
/**
 * UUID
 */
team_id: string
person_id: string
}
export interface TeamAddMemberResult {

}
export interface TeamCreateParams {
name: string
/**
 * UUID
 */
parent_id?: string
}
export interface TeamCreateResult {
/**
 * UUID
 */
team_id: string
}
export interface TeamEffectiveMembersParams {
/**
 * UUID
 */
team_id: string
}
export interface TeamEffectiveMembersResult {
members: {
person_id: string
name: string
}[]
}
export interface TeamEffectiveTeamsParams {
person_id?: string
}
export interface TeamEffectiveTeamsResult {
teams: {
/**
 * UUID
 */
team_id: string
name: string
parent_id: (string | null)
}[]
}
export interface Operations {
  "ai.ask": { params: AiAskParams; result: AiAskResult };
  "appointment.cancel": { params: AppointmentCancelParams; result: AppointmentCancelResult };
  "appointment.create": { params: AppointmentCreateParams; result: AppointmentCreateResult };
  "appointment.get": { params: AppointmentGetParams; result: AppointmentGetResult };
  "appointment.list": { params: AppointmentListParams; result: AppointmentListResult };
  "appointment.reschedule": { params: AppointmentRescheduleParams; result: AppointmentRescheduleResult };
  "cost.list": { params: CostListParams; result: CostListResult };
  "history.list": { params: HistoryListParams; result: HistoryListResult };
  "history.undo": { params: HistoryUndoParams; result: HistoryUndoResult };
  "notification.list": { params: NotificationListParams; result: NotificationListResult };
  "notification.set_channels": { params: NotificationSetChannelsParams; result: NotificationSetChannelsResult };
  "notification.subscribe_push": { params: NotificationSubscribePushParams; result: NotificationSubscribePushResult };
  "notification.test_push": { params: NotificationTestPushParams; result: NotificationTestPushResult };
  "series.create": { params: SeriesCreateParams; result: SeriesCreateResult };
  "series.occurrences": { params: SeriesOccurrencesParams; result: SeriesOccurrencesResult };
  "team.add_member": { params: TeamAddMemberParams; result: TeamAddMemberResult };
  "team.create": { params: TeamCreateParams; result: TeamCreateResult };
  "team.effective_members": { params: TeamEffectiveMembersParams; result: TeamEffectiveMembersResult };
  "team.effective_teams": { params: TeamEffectiveTeamsParams; result: TeamEffectiveTeamsResult };
}
