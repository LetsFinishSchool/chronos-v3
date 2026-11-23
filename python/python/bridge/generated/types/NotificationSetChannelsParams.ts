export interface NotificationSetChannelsParams {
  /**
   * @minItems 1
   */
  channels: ["mock" | "email" | "webpush", ...("mock" | "email" | "webpush")[]];
}
