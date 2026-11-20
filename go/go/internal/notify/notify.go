// Package notify enthält die Operationen rund um Benachrichtigung und Kosten. Es kennt die Kanal-Implementierungen
// nicht; Kanalnamen sind nur Daten.
package notify

import (
	"encoding/json"

	"chronos/internal/db/sqlc"
	"chronos/internal/op"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
)

const tsLayout = "2006-01-02T15:04:05Z"

type SetChannelsParams struct {
	Channels []string `json:"channels" minItems:"1" uniqueItems:"true" enum:"mock,email,webpush" doc:"Geordnete Kanalliste; der erste Kanal wird zuerst versucht, danach die Ersatzkanäle"`
}

type SubscribePushParams struct {
	Endpoint string `json:"endpoint" pattern:"^https://[^ ]+$" doc:"https-URL des Push-Dienstes"`
	P256dh   string `json:"p256dh" minLength:"1"`
	Auth     string `json:"auth" minLength:"1"`
}
type TestPushResult struct {
	EventID string `json:"event_id"`
}

type ListParams struct {
	EventID       *string `json:"event_id,omitempty" format:"uuid"`
	CorrelationID *string `json:"correlation_id,omitempty"`
	Limit         *int    `json:"limit,omitempty" minimum:"1" maximum:"500" doc:"Standard 100"`
}
type Trigger struct {
	Kind  string `json:"kind"`
	Actor string `json:"actor"`
}
type Delivery struct {
	EventID        string  `json:"event_id"`
	EventType      string  `json:"event_type"`
	CorrelationID  string  `json:"correlation_id"`
	Trigger        Trigger `json:"trigger"`
	Recipient      string  `json:"recipient"`
	Channel        string  `json:"channel"`
	Attempt        int     `json:"attempt"`
	Result         string  `json:"result" enum:"success,failed,skipped"`
	Error          *string `json:"error,omitempty"`
	At             string  `json:"at"`
	IdempotencyKey string  `json:"idempotency_key"`
}
type ListResult struct {
	Deliveries []Delivery `json:"deliveries"`
}

type CostListParams struct {
	Limit *int `json:"limit,omitempty" minimum:"1" maximum:"1000" doc:"Standard 100"`
}
type CostTrigger struct {
	Kind          string `json:"kind"`
	Name          string `json:"name"`
	CorrelationID string `json:"correlation_id"`
}
type CostEntry struct {
	ID             string         `json:"id"`
	At             string         `json:"at"`
	PersonID       string         `json:"person_id"`
	Provider       string         `json:"provider" enum:"anthropic,smtp"`
	Trigger        CostTrigger    `json:"trigger"`
	Quantity       map[string]any `json:"quantity"`
	AmountMicroEur int64          `json:"amount_micro_eur"`
}
type CostListResult struct {
	Entries []CostEntry `json:"entries"`
}

func Register(r *op.Registry) {
	op.Register(r, op.Op{Name: "notification.set_channels", Mutating: true,
		Description: "Legt die Benachrichtigungskanäle des Aufrufers fest (geordnet; mock, email, webpush)."},
		func(c *op.Ctx, p SetChannelsParams) (op.Empty, error) {
			if err := c.Q.SetChannels(c.Context, sqlc.SetChannelsParams{ID: c.Caller.ID, Channels: p.Channels}); err != nil {
				return op.Empty{}, err
			}
			return op.Empty{}, nil
		})

	op.Register(r, op.Op{Name: "notification.subscribe_push", Mutating: true,
		Description: "Speichert ein Web-Push-Abonnement des Aufrufers."},
		func(c *op.Ctx, p SubscribePushParams) (op.Empty, error) {
			return op.Empty{}, c.Q.AddPushSubscription(c.Context, sqlc.AddPushSubscriptionParams{PersonID: c.Caller.ID,
				Endpoint: p.Endpoint, P256dh: p.P256dh, Auth: p.Auth})
		})

	op.Register(r, op.Op{Name: "notification.test_push", Mutating: true,
		Description: "Erzeugt ein Testereignis nur für den Aufrufer, das ausschließlich per Web Push zugestellt wird."},
		func(c *op.Ctx, _ op.Empty) (TestPushResult, error) {
			if err := c.Emit("notification.test", []string{c.Caller.ID}, "webpush"); err != nil {
				return TestPushResult{}, err
			}
			return TestPushResult{EventID: c.EventID.String()}, nil
		})

	op.Register(r, op.Op{Name: "notification.list",
		Description: "Zustellprotokoll: je Versuch eine Zeile, für Ereignisse, die der Aufrufer ausgelöst hat oder bei denen er Empfänger ist (älteste zuerst)."},
		func(c *op.Ctx, p ListParams) (ListResult, error) {
			arg := sqlc.ListDeliveriesParams{PersonID: c.Caller.ID, MaxRows: 100}
			if p.CorrelationID != nil {
				arg.CorrelationID = pgtype.Text{String: *p.CorrelationID, Valid: true}
			}
			if p.Limit != nil {
				arg.MaxRows = int32(*p.Limit)
			}
			if p.EventID != nil {
				id, err := op.ParseID(*p.EventID, "event_id")
				if err != nil {
					return ListResult{}, err
				}
				arg.EventID = &id
			}
			rows, err := c.Q.ListDeliveries(c.Context, arg)
			if err != nil {
				return ListResult{}, err
			}
			out := make([]Delivery, len(rows))
			for i, d := range rows {
				out[i] = Delivery{EventID: d.EventID.String(), EventType: d.EventType, CorrelationID: d.CorrelationID,
					Trigger: Trigger{Kind: "person", Actor: d.Actor}, Recipient: d.Recipient, Channel: d.Channel, Attempt: int(d.Attempt),
					Result: d.Result, At: d.At.UTC().Format(tsLayout), IdempotencyKey: d.IdempotencyKey}
				if d.Error.Valid {
					e := d.Error.String
					out[i].Error = &e
				}
			}
			return ListResult{Deliveries: out}, nil
		})

	op.Register(r, op.Op{Name: "cost.list",
		Description: "Listet die Kostenposten, die der Aufrufer verursacht hat (neueste zuerst)."},
		func(c *op.Ctx, p CostListParams) (CostListResult, error) {
			limit := int32(100)
			if p.Limit != nil {
				limit = int32(*p.Limit)
			}
			rows, err := c.Q.ListCosts(c.Context, sqlc.ListCostsParams{PersonID: c.Caller.ID, Limit: limit})
			if err != nil {
				return CostListResult{}, err
			}
			out := make([]CostEntry, len(rows))
			for i, k := range rows {
				q := map[string]any{}
				if err := json.Unmarshal(k.Quantity, &q); err != nil {
					return CostListResult{}, err
				}
				out[i] = CostEntry{ID: k.ID.String(), At: k.At.UTC().Format(tsLayout), PersonID: k.PersonID, Provider: k.Provider,
					Trigger: CostTrigger{Kind: k.TriggerKind, Name: k.TriggerName, CorrelationID: k.CorrelationID}, Quantity: q,
					AmountMicroEur: k.AmountMicroEur}
			}
			return CostListResult{Entries: out}, nil
		})
}

// RecordCost schreibt einen Kostenposten (für Aufrufer in Operationen).
func RecordCost(c *op.Ctx, provider string, quantity map[string]any, amount int64) error {
	q, err := json.Marshal(quantity)
	if err != nil {
		return err
	}
	return c.Q.InsertCost(c.Context, sqlc.InsertCostParams{ID: uuid.New(), PersonID: c.Caller.ID, Provider: provider, TriggerKind: "operation",
		TriggerName: c.OpName, CorrelationID: c.CorrelationID, Quantity: q, AmountMicroEur: amount})
}
