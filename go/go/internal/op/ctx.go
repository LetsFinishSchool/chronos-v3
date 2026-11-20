package op

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"

	"chronos/internal/config"
	"chronos/internal/db/sqlc"
)

// Caller ist die authentifizierte Person.
type Caller struct{ ID, Name, Email string }

type callerKey struct{}

func WithCaller(ctx context.Context, c Caller) context.Context {
	return context.WithValue(ctx, callerKey{}, c)
}

func CallerFrom(ctx context.Context) (Caller, bool) {
	c, ok := ctx.Value(callerKey{}).(Caller)
	return c, ok
}

type faultKey struct{}

func WithFault(ctx context.Context, f string) context.Context {
	return context.WithValue(ctx, faultKey{}, f)
}

// Affected beschreibt ein von einer Operation berührtes Objekt (Vorschau).
type Affected struct {
	Type   string `json:"type" doc:"Objektart"`
	ID     string `json:"id" doc:"Objekt-ID"`
	Change string `json:"change" doc:"Beschreibung der Änderung"`
}

// Ctx ist alles, was eine Operation während ihrer Ausführung braucht. Schreibende Operationen laufen in
// genau einer Transaktion (Q gehört dann zur Transaktion); lesende direkt auf dem Pool.
type Ctx struct {
	Context       context.Context
	Q             *sqlc.Queries
	Pool          *pgxpool.Pool
	Cfg           *config.Config
	Caller        Caller
	CorrelationID string
	OpName        string
	BundleID      uuid.UUID
	EventID       uuid.UUID
	fault         string
	affected      []Affected
}

// Affect meldet ein berührtes Objekt (für die Vorschau; bei echter Ausführung ohne Wirkung).
func (c *Ctx) Affect(typ string, id uuid.UUID, change string) {
	c.affected = append(c.affected, Affected{Type: typ, ID: id.String(), Change: change})
}

// IsMember prüft effektive Mitgliedschaft des Aufrufers (Team oder Unter-Team).
func (c *Ctx) RequireMember(team uuid.UUID) error {
	if _, err := c.Q.GetTeam(c.Context, team); err != nil {
		return NotFoundIf(err, "Team")
	}
	ok, err := c.Q.IsEffectiveMember(c.Context, sqlc.IsEffectiveMemberParams{ID: team, PersonID: c.Caller.ID})
	if err != nil {
		return err
	}
	if !ok {
		return Forbidden("kein Mitglied des Teams")
	}
	return nil
}

// HistoryInput beschreibt einen Verlaufseintrag.
type HistoryInput struct {
	Action     string
	ObjectType string
	ObjectID   uuid.UUID
	TeamID     uuid.UUID
	Before     any // nil = nicht vorhanden
	After      any
	UndoOf     *uuid.UUID
	WithEvent  bool // der Eintrag gehört zum Ereignis dieser Operation (Emit)
}

func marshalState(v any) ([]byte, error) {
	if v == nil {
		return nil, nil
	}
	if raw, ok := v.(json.RawMessage); ok {
		return raw, nil
	}
	return json.Marshal(v)
}

// Record schreibt den Verlaufseintrag in der Transaktion der Operation.
func (c *Ctx) Record(h HistoryInput) (uuid.UUID, error) {
	before, err := marshalState(h.Before)
	if err != nil {
		return uuid.Nil, err
	}
	after, err := marshalState(h.After)
	if err != nil {
		return uuid.Nil, err
	}
	id := uuid.New()
	var ev *uuid.UUID
	if h.WithEvent {
		e := c.EventID
		ev = &e
	}
	err = c.Q.InsertHistory(c.Context, sqlc.InsertHistoryParams{
		ID: id, Actor: c.Caller.ID, Action: h.Action, ObjectType: h.ObjectType, ObjectID: h.ObjectID, TeamID: h.TeamID,
		Before: before, After: after, BundleID: c.BundleID, CorrelationID: c.CorrelationID, UndoOf: h.UndoOf, EventID: ev,
	})
	return id, err
}

var errInjected = errors.New("injected fault after_history")

// Emit schreibt das Ereignis samt Empfängern in derselben Transaktion (Auslöser = Aufrufer).
func (c *Ctx) Emit(eventType string, recipients []string, forcedChannel string) error {
	if c.fault == "after_history" {
		return errInjected
	}
	fc := pgxText(forcedChannel)
	if err := c.Q.InsertEvent(c.Context, sqlc.InsertEventParams{
		ID: c.EventID, Type: eventType, Actor: c.Caller.ID, Operation: c.OpName, CorrelationID: c.CorrelationID, ForcedChannel: fc,
	}); err != nil {
		return err
	}
	if len(recipients) == 0 {
		return nil
	}
	return c.Q.InsertRecipients(c.Context, sqlc.InsertRecipientsParams{EventID: c.EventID, Recipients: recipients})
}

// RecipientsExceptCaller: alle effektiven Mitglieder des Teams außer dem Aufrufer.
func (c *Ctx) RecipientsExceptCaller(team uuid.UUID) ([]string, error) {
	ms, err := c.Q.EffectiveMembers(c.Context, team)
	if err != nil {
		return nil, err
	}
	out := make([]string, 0, len(ms))
	for _, m := range ms {
		if m.PersonID != c.Caller.ID {
			out = append(out, m.PersonID)
		}
	}
	return out, nil
}

// ParseID prüft eine UUID aus den Parametern.
func ParseID(s, what string) (uuid.UUID, error) {
	id, err := uuid.Parse(s)
	if err != nil {
		return uuid.Nil, Validation("%s ist keine UUID", what)
	}
	return id, nil
}

func pgxText(s string) pgtype.Text { return pgtype.Text{String: s, Valid: s != ""} }
