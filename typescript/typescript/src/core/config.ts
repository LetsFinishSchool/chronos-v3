const env = process.env;
const int = (v: string | undefined, d: number) => (v && /^\d+$/.test(v) ? Number(v) : d);

export const config = {
  databaseUrl: env.DATABASE_URL ?? "postgres://chronos:chronos@localhost:5432/chronos",
  port: int(env.PORT, 8080),
  workerHealthPort: int(env.WORKER_HEALTH_PORT, 8081),
  oidc: {
    issuer: env.OIDC_ISSUER_URL ?? "",
    clientId: env.OIDC_CLIENT_ID ?? "",
    clientSecret: env.OIDC_CLIENT_SECRET ?? "",
    redirectUrl: env.OIDC_REDIRECT_URL ?? "",
  },
  smtp: { host: env.SMTP_HOST ?? "localhost", port: int(env.SMTP_PORT, 1025) },
  vapid: { publicKey: env.VAPID_PUBLIC_KEY ?? "", privateKey: env.VAPID_PRIVATE_KEY ?? "", subject: env.VAPID_SUBJECT ?? "mailto:spike@example.test" },
  mockChannelUrl: env.MOCK_CHANNEL_URL ?? "http://localhost:8090",
  ai: {
    baseUrl: env.ANTHROPIC_BASE_URL || undefined,
    apiKey: env.ANTHROPIC_API_KEY ?? "",
    model: env.ANTHROPIC_MODEL ?? "claude-haiku-5-5",
    priceInMicroEurPerMtok: int(env.AI_PRICE_IN_MICRO_EUR_PER_MTOK, 0),
    priceOutMicroEurPerMtok: int(env.AI_PRICE_OUT_MICRO_EUR_PER_MTOK, 0),
  },
  emailPriceMicroEur: int(env.EMAIL_PRICE_MICRO_EUR, 0),
  retryBaseMs: int(env.RETRY_BASE_MS, 1000),
  staticDir: env.STATIC_DIR,
  faults: env.SPIKE_FAULTS === "1",
  workerConcurrency: int(env.WORKER_CONCURRENCY, 8),
};
