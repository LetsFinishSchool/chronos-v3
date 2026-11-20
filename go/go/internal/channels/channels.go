// Package channels enthält die Zustellkanäle mock, email und webpush. Die Fachbereiche (internal/domain) kennen es nicht.
package channels

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"

	webpush "github.com/SherClockHolmes/webpush-go"
	mail "github.com/wneessen/go-mail"

	"chronos/internal/config"
)

// ErrSkipped: dem Empfänger fehlt die Voraussetzung für den Kanal (z. B. kein Push-Abo).
var ErrSkipped = errors.New("Voraussetzung fehlt")

// Message ist eine Zustellung an einen Empfänger.
type Message struct {
	EventID        string
	EventType      string
	CorrelationID  string
	Recipient      string
	Email          string
	IdempotencyKey string
	Subscriptions  []Subscription
}

type Subscription struct{ Endpoint, P256dh, Auth string }

type Channel interface {
	Send(ctx context.Context, m Message) error
}

// New liefert die Kanäle nach Name.
func New(cfg *config.Config) map[string]Channel {
	return map[string]Channel{
		"mock":    &Mock{URL: cfg.MockChannelURL, HTTP: &http.Client{Timeout: 10 * time.Second}},
		"email":   &Email{Host: cfg.SMTPHost, Port: cfg.SMTPPort},
		"webpush": &WebPush{Public: cfg.VapidPublicKey, Private: cfg.VapidPrivateKey, Subject: cfg.VapidSubject},
	}
}

type Mock struct {
	URL  string
	HTTP *http.Client
}

func (c *Mock) Send(ctx context.Context, m Message) error {
	body, _ := json.Marshal(map[string]string{"recipient": m.Recipient, "event_type": m.EventType, "event_id": m.EventID, "correlation_id": m.CorrelationID})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.URL+"/deliver", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", m.IdempotencyKey)
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, resp.Body)
	if resp.StatusCode/100 != 2 {
		return fmt.Errorf("Mock-Kanal antwortete %d", resp.StatusCode)
	}
	return nil
}

type Email struct {
	Host string
	Port int
}

func (c *Email) Send(ctx context.Context, m Message) error {
	if m.Email == "" {
		return ErrSkipped
	}
	msg := mail.NewMsg()
	if err := msg.From("chronos-spike@example.test"); err != nil {
		return err
	}
	if err := msg.To(m.Email); err != nil {
		return err
	}
	msg.Subject("Chronos: " + m.EventType)
	msg.SetGenHeader(mail.Header("X-Chronos-Idempotency-Key"), m.IdempotencyKey)
	msg.SetGenHeader(mail.Header("X-Chronos-Correlation-Id"), m.CorrelationID)
	msg.SetBodyString(mail.TypeTextPlain, fmt.Sprintf("Ereignis %s (%s)", m.EventType, m.EventID))
	cl, err := mail.NewClient(c.Host, mail.WithPort(c.Port), mail.WithTLSPolicy(mail.NoTLS))
	if err != nil {
		return err
	}
	return cl.DialAndSendWithContext(ctx, msg)
}

type WebPush struct{ Public, Private, Subject string }

func (c *WebPush) Send(ctx context.Context, m Message) error {
	if len(m.Subscriptions) == 0 {
		return ErrSkipped
	}
	payload, _ := json.Marshal(map[string]string{"event_type": m.EventType, "event_id": m.EventID})
	var ok int
	var last error
	for _, s := range m.Subscriptions {
		sub := &webpush.Subscription{Endpoint: s.Endpoint, Keys: webpush.Keys{P256dh: s.P256dh, Auth: s.Auth}}
		resp, err := webpush.SendNotificationWithContext(ctx, payload, sub, &webpush.Options{
			Subscriber: c.Subject, VAPIDPublicKey: c.Public, VAPIDPrivateKey: c.Private, TTL: 60, Topic: "",
		})
		if err != nil {
			last = err
			continue
		}
		_, _ = io.Copy(io.Discard, resp.Body)
		resp.Body.Close()
		if resp.StatusCode/100 != 2 {
			last = fmt.Errorf("Push-Dienst antwortete %d", resp.StatusCode)
			continue
		}
		ok++
	}
	if ok == 0 {
		return last
	}
	return nil
}
