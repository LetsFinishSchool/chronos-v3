// Package config liest die Umgebungsvariablen aus V-1 §2.
package config

import (
	"os"
	"strconv"
)

type Config struct {
	DatabaseURL       string
	Port              string
	WorkerHealthPort  string
	OIDCIssuer        string
	OIDCClientID      string
	OIDCClientSecret  string
	OIDCRedirectURL   string
	SMTPHost          string
	SMTPPort          int
	VapidPublicKey    string
	VapidPrivateKey   string
	VapidSubject      string
	MockChannelURL    string
	AnthropicBaseURL  string
	AnthropicAPIKey   string
	AnthropicModel    string
	AIPriceInMicro    int64
	AIPriceOutMicro   int64
	EmailPriceMicro   int64
	RetryBaseMS       int
	StaticDir         string
	Faults            bool
	LogFormat         string
	WorkerConcurrency int
}

func Load() Config {
	return Config{
		DatabaseURL:       env("DATABASE_URL", "postgres://chronos:chronos@localhost:5432/chronos"),
		Port:              env("PORT", "8080"),
		WorkerHealthPort:  env("WORKER_HEALTH_PORT", "8081"),
		OIDCIssuer:        env("OIDC_ISSUER_URL", ""),
		OIDCClientID:      env("OIDC_CLIENT_ID", ""),
		OIDCClientSecret:  env("OIDC_CLIENT_SECRET", ""),
		OIDCRedirectURL:   env("OIDC_REDIRECT_URL", ""),
		SMTPHost:          env("SMTP_HOST", "localhost"),
		SMTPPort:          int(num("SMTP_PORT", 1025)),
		VapidPublicKey:    env("VAPID_PUBLIC_KEY", ""),
		VapidPrivateKey:   env("VAPID_PRIVATE_KEY", ""),
		VapidSubject:      env("VAPID_SUBJECT", "mailto:spike@example.test"),
		MockChannelURL:    env("MOCK_CHANNEL_URL", ""),
		AnthropicBaseURL:  env("ANTHROPIC_BASE_URL", ""),
		AnthropicAPIKey:   env("ANTHROPIC_API_KEY", ""),
		AnthropicModel:    env("ANTHROPIC_MODEL", ""),
		AIPriceInMicro:    num("AI_PRICE_IN_MICRO_EUR_PER_MTOK", 0),
		AIPriceOutMicro:   num("AI_PRICE_OUT_MICRO_EUR_PER_MTOK", 0),
		EmailPriceMicro:   num("EMAIL_PRICE_MICRO_EUR", 0),
		RetryBaseMS:       int(num("RETRY_BASE_MS", 1000)),
		StaticDir:         env("STATIC_DIR", ""),
		Faults:            os.Getenv("SPIKE_FAULTS") == "1",
		LogFormat:         env("LOG_FORMAT", "json"),
		WorkerConcurrency: int(num("WORKER_CONCURRENCY", 8)),
	}
}

func env(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func num(k string, def int64) int64 {
	if v, err := strconv.ParseInt(os.Getenv(k), 10, 64); err == nil {
		return v
	}
	return def
}
