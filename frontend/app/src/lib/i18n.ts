// Einstiegspunkt für Texte (V-3): #47 ersetzt nur diese Datei durch den Fluent-Katalog.
const catalog = {
  "start.title": "Chronos",
  "start.intro": "Termine im Leitungsteam planen und Rückmeldungen einholen.",
  "error.not-found.title": "Seite nicht gefunden",
  "error.not-found.text": "Diese Adresse gibt es in Chronos nicht.",
  "error.home": "Zur Startseite",
  "error.generic.title": "Etwas ist schiefgegangen",
  "error.generic.text": "Die Seite konnte nicht angezeigt werden. Bitte versuche es erneut.",
} as const;

export type MessageKey = keyof typeof catalog;

export function t(key: MessageKey): string {
  return catalog[key];
}
