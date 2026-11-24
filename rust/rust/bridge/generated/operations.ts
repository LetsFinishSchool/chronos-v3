// GENERIERT aus GET /api/v1/operations (make bridge); nicht von Hand ändern.

export interface AiAskParams {
prompt: string
team_id?: string
}
export interface AiAskResult {
proposed_calls: {
input: {

}
name: string
}[]
text: string
usage: {
input_tokens: number
output_tokens: number
}
}
export interface AppointmentCancelParams {
appointment_id: string
}
export interface AppointmentCancelResult {

}
export interface AppointmentCreateParams {
ends_at: string
starts_at: string
team_id: string
/**
 * IANA-Zeitzonenname, z. B. Europe/Berlin
 */
timezone: string
title: string
}
export interface AppointmentCreateResult {
appointment_id: string
}
export interface AppointmentGetParams {
appointment_id: string
}
export interface AppointmentGetResult {
appointment: {
ends_at: string
id: string
starts_at: string
status: string
team_id: string
timezone: string
title: string
}
}
export interface AppointmentListParams {
team_id: string
}
export interface AppointmentListResult {
appointments: {
ends_at: string
id: string
starts_at: string
status: string
team_id: string
timezone: string
title: string
}[]
}
export interface AppointmentRescheduleParams {
appointment_id: string
ends_at: string
starts_at: string
}
export interface AppointmentRescheduleResult {

}
export interface CostListParams {
limit?: number
}
export interface CostListResult {
entries: {
amount_micro_eur: number
at: string
id: string
person_id: string
/**
 * anthropic oder smtp
 */
provider: string
quantity: {

}
trigger: {
correlation_id: string
kind: string
name: string
}
}[]
}
export interface HistoryListParams {
limit?: number
object_id?: string
}
export interface HistoryListResult {
entries: {
action: string
actor: string
after?: ({

} | null)
at: string
before?: ({

} | null)
bundle_id: string
correlation_id: string
id: string
object_id: string
object_type: string
undo_of?: (string | null)
undone: boolean
}[]
}
export interface HistoryUndoParams {
history_id: string
}
export interface HistoryUndoResult {
history_id: string
}
export interface NotificationListParams {
correlation_id?: string
event_id?: string
limit?: number
}
export interface NotificationListResult {
deliveries: {
at: string
attempt: number
channel: string
correlation_id: string
error?: (string | null)
event_id: string
event_type: string
idempotency_key: string
recipient: string
/**
 * success, failed oder skipped
 */
result: string
trigger: {
actor: string
kind: string
}
}[]
}
export interface NotificationSetChannelsParams {
/**
 * Geordnete Liste; der erste Kanal wird zuerst versucht, die folgenden dienen als Ersatz.
 * 
 * @minItems 1
 */
channels: [("mock" | "email" | "webpush"), ...(("mock" | "email" | "webpush"))[]]
}
export interface NotificationSetChannelsResult {

}
export interface NotificationSubscribePushParams {
auth: string
endpoint: string
p256dh: string
}
export interface NotificationSubscribePushResult {

}
export interface NotificationTestPushParams {

}
export interface NotificationTestPushResult {
event_id: string
}
export interface SeriesCreateParams {
/**
 * Ortszeit, z. B. 2026-03-02T18:00:00
 */
dtstart: string
duration_minutes: number
/**
 * Ausgenommene Vorkommen als Ortszeiten
 */
exdates?: string[]
/**
 * RRULE ohne Präfix `RRULE:`
 */
rrule: string
team_id: string
/**
 * IANA-Zeitzonenname
 */
timezone: string
title: string
}
export interface SeriesCreateResult {
series_id: string
}
export interface SeriesOccurrencesParams {
from: string
series_id: string
to: string
}
export interface SeriesOccurrencesResult {
occurrences: {
ends_at: string
starts_at: string
}[]
}
export interface TeamAddMemberParams {
person_id: string
team_id: string
}
export interface TeamAddMemberResult {

}
export interface TeamCreateParams {
name: string
parent_id?: string
}
export interface TeamCreateResult {
team_id: string
}
export interface TeamEffectiveMembersParams {
team_id: string
}
export interface TeamEffectiveMembersResult {
members: {
name: string
person_id: string
}[]
}
export interface TeamEffectiveTeamsParams {
person_id?: string
}
export interface TeamEffectiveTeamsResult {
teams: {
name: string
parent_id?: (string | null)
team_id: string
}[]
}
export interface OperationMap {
  "ai.ask": { params: AiAskParams; result: AiAskResult; mutating: false; preview: false };
  "appointment.cancel": { params: AppointmentCancelParams; result: AppointmentCancelResult; mutating: true; preview: true };
  "appointment.create": { params: AppointmentCreateParams; result: AppointmentCreateResult; mutating: true; preview: true };
  "appointment.get": { params: AppointmentGetParams; result: AppointmentGetResult; mutating: false; preview: false };
  "appointment.list": { params: AppointmentListParams; result: AppointmentListResult; mutating: false; preview: false };
  "appointment.reschedule": { params: AppointmentRescheduleParams; result: AppointmentRescheduleResult; mutating: true; preview: true };
  "cost.list": { params: CostListParams; result: CostListResult; mutating: false; preview: false };
  "history.list": { params: HistoryListParams; result: HistoryListResult; mutating: false; preview: false };
  "history.undo": { params: HistoryUndoParams; result: HistoryUndoResult; mutating: true; preview: true };
  "notification.list": { params: NotificationListParams; result: NotificationListResult; mutating: false; preview: false };
  "notification.set_channels": { params: NotificationSetChannelsParams; result: NotificationSetChannelsResult; mutating: true; preview: false };
  "notification.subscribe_push": { params: NotificationSubscribePushParams; result: NotificationSubscribePushResult; mutating: true; preview: false };
  "notification.test_push": { params: NotificationTestPushParams; result: NotificationTestPushResult; mutating: true; preview: false };
  "series.create": { params: SeriesCreateParams; result: SeriesCreateResult; mutating: true; preview: false };
  "series.occurrences": { params: SeriesOccurrencesParams; result: SeriesOccurrencesResult; mutating: false; preview: false };
  "team.add_member": { params: TeamAddMemberParams; result: TeamAddMemberResult; mutating: true; preview: false };
  "team.create": { params: TeamCreateParams; result: TeamCreateResult; mutating: true; preview: false };
  "team.effective_members": { params: TeamEffectiveMembersParams; result: TeamEffectiveMembersResult; mutating: false; preview: false };
  "team.effective_teams": { params: TeamEffectiveTeamsParams; result: TeamEffectiveTeamsResult; mutating: false; preview: false };
}

export type OperationName = keyof OperationMap;
