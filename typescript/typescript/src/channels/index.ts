import type { ChannelName } from "../core/channels.js";
import { emailChannel } from "./email.js";
import { mockChannel } from "./mock.js";
import type { Channel } from "./types.js";
import { webpushChannel } from "./webpush.js";

export const channels: Record<ChannelName, Channel> = { mock: mockChannel, email: emailChannel, webpush: webpushChannel };
export type { Channel, DeliveryRequest } from "./types.js";
