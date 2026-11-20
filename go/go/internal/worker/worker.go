// Package worker stellt festgehaltene Ereignisse zu. Es liest ausschließlich aus der Datenbank (V-1 §5): Je
// Ereignis und Empfänger gibt es eine Zeile in event_recipients; der Worker beansprucht sie (FOR UPDATE SKIP LOCKED,
// mit Ablaufzeit), stellt über die Kanäle zu und schreibt je Versuch eine Zeile in deliveries.
package worker

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"

	"chronos/internal/channels"
	"chronos/internal/config"
	"chronos/internal/db/sqlc"
	"chronos/internal/logx"
)

const (
	maxAttempts = 3
	leaseSecs   = 120
)

type Worker struct {
	Pool     *pgxpool.Pool
	Q        *sqlc.Queries
	Cfg      *config.Config
	Channels map[string]channels.Channel
}

func New(pool *pgxpool.Pool, cfg *config.Config) *Worker {
	return &Worker{Pool: pool, Q: sqlc.New(pool), Cfg: cfg, Channels: channels.New(cfg)}
}

// EIGENBAU:BEGIN Auftragsschleife über die Tabelle event_recipients (Outbox mit SKIP LOCKED); eine Auftragsbibliothek
// (z. B. River) wäre für den Spike größer gewesen als dieser Block.
func (w *Worker) Run(ctx context.Context) error {
	if err := w.Q.ResetClaims(ctx); err != nil { // Neustart nach SIGKILL: unfertige Zustellungen sofort wieder freigeben
		return err
	}
	slog.InfoContext(ctx, "Worker gestartet", "concurrency", w.Cfg.WorkerConcurrency)
	slots := make(chan struct{}, w.Cfg.WorkerConcurrency)
	for ctx.Err() == nil {
		free := cap(slots) - len(slots)
		if free == 0 {
			sleep(ctx, 10*time.Millisecond)
			continue
		}
		rows, err := w.Q.ClaimRecipients(ctx, sqlc.ClaimRecipientsParams{LeaseSecs: leaseSecs, MaxRows: int32(free)})
		if err != nil {
			slog.ErrorContext(ctx, "Beanspruchen fehlgeschlagen", "error", err.Error())
			sleep(ctx, time.Second)
			continue
		}
		if len(rows) == 0 {
			sleep(ctx, 150*time.Millisecond)
			continue
		}
		for _, r := range rows {
			slots <- struct{}{}
			go func() {
				defer func() { <-slots }()
				ectx := logx.WithEvent(ctx, r.EventID.String())
				if err := w.deliver(ectx, r.EventID, r.Recipient); err != nil && ctx.Err() == nil {
					slog.ErrorContext(ectx, "Zustellung abgebrochen, wird später fortgesetzt", "recipient", r.Recipient, "error", err.Error())
				}
			}()
		}
	}
	return ctx.Err()
}

func sleep(ctx context.Context, d time.Duration) {
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-ctx.Done():
	case <-t.C:
	}
}

// deliver stellt einem Empfänger zu. Der Zustand folgt aus den Zeilen in deliveries, daher setzt ein Neustart
// genau dort fort, wo die letzte Instanz aufgehört hat (Idempotenzschlüssel bleiben gleich).
func (w *Worker) deliver(ctx context.Context, eventID uuid.UUID, recipient string) error {
	ev, err := w.Q.GetEvent(ctx, eventID)
	if err != nil {
		return err
	}
	ctx = logx.WithCorrelation(ctx, ev.CorrelationID)
	person, err := w.Q.GetPerson(ctx, recipient)
	if err != nil {
		return err
	}
	order := person.Channels
	if ev.ForcedChannel.Valid {
		order = []string{ev.ForcedChannel.String}
	}
	rows, err := w.Q.DeliveriesFor(ctx, sqlc.DeliveriesForParams{EventID: eventID, Recipient: recipient})
	if err != nil {
		return err
	}
	failed, skipped := map[string]int{}, map[string]bool{}
	for _, d := range rows {
		switch d.Result {
		case "success":
			return w.Q.FinishRecipient(ctx, sqlc.FinishRecipientParams{EventID: eventID, Recipient: recipient})
		case "failed":
			failed[d.Channel]++
		case "skipped":
			skipped[d.Channel] = true
		}
	}
	subs, err := w.Q.ListPushSubscriptions(ctx, recipient)
	if err != nil {
		return err
	}
	msg := channels.Message{EventID: eventID.String(), EventType: ev.Type, CorrelationID: ev.CorrelationID, Recipient: recipient, Email: person.Email}
	for _, s := range subs {
		msg.Subscriptions = append(msg.Subscriptions, channels.Subscription{Endpoint: s.Endpoint, P256dh: s.P256dh, Auth: s.Auth})
	}
	base := time.Duration(w.Cfg.RetryBaseMS) * time.Millisecond
	for _, name := range order {
		ch, ok := w.Channels[name]
		if !ok || skipped[name] {
			continue
		}
		msg.IdempotencyKey = fmt.Sprintf("%s:%s:%s", eventID, recipient, name)
		for attempt := failed[name] + 1; attempt <= maxAttempts; attempt++ {
			if attempt > 1 {
				sleep(ctx, base<<(attempt-2))
				if ctx.Err() != nil {
					return ctx.Err()
				}
			}
			sctx, cancel := context.WithTimeout(ctx, 20*time.Second)
			err := ch.Send(sctx, msg)
			cancel()
			result, errText := "success", pgtype.Text{}
			switch {
			case errors.Is(err, channels.ErrSkipped):
				result, errText = "skipped", pgtype.Text{String: err.Error(), Valid: true}
			case err != nil:
				result, errText = "failed", pgtype.Text{String: err.Error(), Valid: true}
			}
			if ctx.Err() != nil {
				return ctx.Err()
			}
			if err := w.record(ctx, ev, recipient, name, attempt, result, errText, msg.IdempotencyKey); err != nil {
				return err
			}
			slog.InfoContext(ctx, "Zustellversuch", "recipient", recipient, "channel", name, "attempt", attempt, "result", result)
			if result == "success" {
				return w.Q.FinishRecipient(ctx, sqlc.FinishRecipientParams{EventID: eventID, Recipient: recipient})
			}
			if result == "skipped" {
				break
			}
		}
	}
	slog.WarnContext(ctx, "Zustellung endgültig fehlgeschlagen", "recipient", recipient)
	return w.Q.FinishRecipient(ctx, sqlc.FinishRecipientParams{EventID: eventID, Recipient: recipient})
}

// EIGENBAU:END

// record schreibt Versuchszeile und (bei erfolgreicher E-Mail) den Kostenposten atomar.
func (w *Worker) record(ctx context.Context, ev sqlc.Event, recipient, channel string, attempt int, result string, errText pgtype.Text, key string) error {
	tx, err := w.Pool.BeginTx(ctx, pgx.TxOptions{})
	if err != nil {
		return err
	}
	defer tx.Rollback(context.WithoutCancel(ctx)) //nolint:errcheck
	q := w.Q.WithTx(tx)
	if err := q.InsertDelivery(ctx, sqlc.InsertDeliveryParams{EventID: ev.ID, Recipient: recipient, Channel: channel, Attempt: int32(attempt),
		Result: result, Error: errText, IdempotencyKey: key}); err != nil {
		return err
	}
	if result == "success" && channel == "email" {
		qty, _ := json.Marshal(map[string]int{"messages": 1})
		if err := q.InsertCost(ctx, sqlc.InsertCostParams{ID: uuid.New(), PersonID: ev.Actor, Provider: "smtp", TriggerKind: "operation",
			TriggerName: ev.Operation, CorrelationID: ev.CorrelationID, Quantity: qty, AmountMicroEur: w.Cfg.EmailPriceMicro}); err != nil {
			return err
		}
	}
	return tx.Commit(ctx)
}

// WaitForSchema wartet bis zu 60 s auf die Migrationen des Web.
func WaitForSchema(ctx context.Context, pool *pgxpool.Pool, wantVersion int64) error {
	deadline := time.Now().Add(60 * time.Second)
	for {
		var v int64
		err := pool.QueryRow(ctx, `SELECT COALESCE(max(version_id), 0) FROM goose_db_version WHERE is_applied`).Scan(&v)
		if err == nil && v >= wantVersion {
			return nil
		}
		if time.Now().After(deadline) {
			return fmt.Errorf("Schema nach 60 s nicht bereit (Version %d, erwartet %d): %v", v, wantVersion, err)
		}
		sleep(ctx, time.Second)
	}
}

// Health bietet GET /healthz des Workers.
func Health(pool *pgxpool.Pool) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if err := pool.Ping(r.Context()); err != nil {
			w.WriteHeader(http.StatusServiceUnavailable)
			_, _ = w.Write([]byte(`{"status":"unavailable"}`))
			return
		}
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	})
	return mux
}
