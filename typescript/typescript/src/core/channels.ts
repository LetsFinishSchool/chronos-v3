/** Kanalnamen: gemeinsamer Vertrag zwischen Fachbereichen und Kanälen (kein Import der Kanalimplementierungen). */
export const CHANNEL_NAMES = ["mock", "email", "webpush"] as const;
export type ChannelName = (typeof CHANNEL_NAMES)[number];
