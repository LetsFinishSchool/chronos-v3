package domain

import (
	"encoding/json"

	"chronos/internal/db/sqlc"
	"chronos/internal/op"
)

type HistoryListParams struct {
	ObjectID *string `json:"object_id,omitempty" format:"uuid" doc:"Nur Einträge zu diesem Objekt"`
	Limit    *int    `json:"limit,omitempty" minimum:"1" maximum:"200" doc:"Standard 50"`
}
type HistoryEntry struct {
	ID            string         `json:"id"`
	At            string         `json:"at"`
	Actor         string         `json:"actor" doc:"Keycloak-sub des Auslösers"`
	Action        string         `json:"action"`
	ObjectType    string         `json:"object_type"`
	ObjectID      string         `json:"object_id"`
	Before        map[string]any `json:"before" nullable:"true" doc:"Zustand vor der Änderung, null bei Anlage"`
	After         map[string]any `json:"after" nullable:"true" doc:"Zustand nach der Änderung"`
	BundleID      string         `json:"bundle_id"`
	CorrelationID string         `json:"correlation_id"`
	Undone        bool           `json:"undone"`
	UndoOf        *string        `json:"undo_of" nullable:"true"`
}
type HistoryListResult struct {
	Entries []HistoryEntry `json:"entries"`
}
type HistoryUndoParams struct {
	HistoryID string `json:"history_id" format:"uuid"`
}
type HistoryUndoResult struct {
	HistoryID string `json:"history_id" doc:"Der neue Verlaufseintrag"`
}

func toMap(raw []byte) (map[string]any, error) {
	if raw == nil {
		return nil, nil
	}
	var m map[string]any
	return m, json.Unmarshal(raw, &m)
}

func entryOf(h sqlc.History) (HistoryEntry, error) {
	before, err := toMap(h.Before)
	if err != nil {
		return HistoryEntry{}, err
	}
	after, err := toMap(h.After)
	if err != nil {
		return HistoryEntry{}, err
	}
	e := HistoryEntry{ID: h.ID.String(), At: h.At.UTC().Format(tsLayout), Actor: h.Actor, Action: h.Action, ObjectType: h.ObjectType,
		ObjectID: h.ObjectID.String(), Before: before, After: after, BundleID: h.BundleID.String(), CorrelationID: h.CorrelationID, Undone: h.Undone}
	if h.UndoOf != nil {
		s := h.UndoOf.String()
		e.UndoOf = &s
	}
	return e, nil
}

func registerHistory(r *op.Registry) {
	op.Register(r, op.Op{Name: "history.list",
		Description: "Listet den Änderungsverlauf (neueste zuerst) der Objekte in Teams, in denen der Aufrufer Mitglied ist."},
		func(c *op.Ctx, p HistoryListParams) (HistoryListResult, error) {
			arg := sqlc.ListHistoryParams{PersonID: c.Caller.ID, MaxRows: 50}
			if p.Limit != nil {
				arg.MaxRows = int32(*p.Limit)
			}
			if p.ObjectID != nil {
				id, err := op.ParseID(*p.ObjectID, "object_id")
				if err != nil {
					return HistoryListResult{}, err
				}
				arg.ObjectID = &id
			}
			rows, err := c.Q.ListHistory(c.Context, arg)
			if err != nil {
				return HistoryListResult{}, err
			}
			out := make([]HistoryEntry, len(rows))
			for i, h := range rows {
				if out[i], err = entryOf(h); err != nil {
					return HistoryListResult{}, err
				}
			}
			return HistoryListResult{Entries: out}, nil
		})

	op.Register(r, op.Op{Name: "history.undo", Mutating: true,
		Description: "Macht eine Änderung rückgängig: stellt den Zustand vor dem Verlaufseintrag wieder her. Nur zulässig, wenn das Objekt noch im Zustand nach dem Eintrag ist."},
		func(c *op.Ctx, p HistoryUndoParams) (HistoryUndoResult, error) {
			id, err := op.ParseID(p.HistoryID, "history_id")
			if err != nil {
				return HistoryUndoResult{}, err
			}
			h, err := c.Q.GetHistory(c.Context, id)
			if err != nil {
				return HistoryUndoResult{}, op.NotFoundIf(err, "Verlaufseintrag")
			}
			if err := c.RequireMember(h.TeamID); err != nil {
				return HistoryUndoResult{}, err
			}
			if h.ObjectType != "appointment" {
				return HistoryUndoResult{}, op.NotUndoable("Objektart %s lässt sich nicht rückgängig machen", h.ObjectType)
			}
			if h.Undone {
				return HistoryUndoResult{}, op.NotUndoable("Eintrag wurde bereits rückgängig gemacht")
			}
			cur, err := c.Q.GetAppointment(c.Context, h.ObjectID)
			if err != nil {
				return HistoryUndoResult{}, op.NotFoundIf(err, "Termin")
			}
			curView := viewOf(cur)
			var after AppointmentView
			if err := json.Unmarshal(h.After, &after); err != nil || after != curView {
				return HistoryUndoResult{}, op.NotUndoable("Der Termin wurde seit diesem Eintrag geändert")
			}
			target := curView
			if h.Before != nil {
				if err := json.Unmarshal(h.Before, &target); err != nil {
					return HistoryUndoResult{}, err
				}
			} else {
				target.Status = statusDeleted
			}
			restored := cur
			restored.Title, restored.Timezone, restored.Status = target.Title, target.Timezone, target.Status
			if restored.StartsAt, err = parseTS(target.StartsAt, "starts_at"); err != nil {
				return HistoryUndoResult{}, err
			}
			if restored.EndsAt, err = parseTS(target.EndsAt, "ends_at"); err != nil {
				return HistoryUndoResult{}, err
			}
			if err := store(c, restored); err != nil {
				return HistoryUndoResult{}, err
			}
			newID, err := c.Record(op.HistoryInput{Action: "history.undo", ObjectType: "appointment", ObjectID: cur.ID, TeamID: cur.TeamID,
				Before: curView, After: target, UndoOf: &h.ID, WithEvent: true})
			if err != nil {
				return HistoryUndoResult{}, err
			}
			if err := c.Q.SetUndone(c.Context, sqlc.SetUndoneParams{ID: h.ID, Undone: true}); err != nil {
				return HistoryUndoResult{}, err
			}
			if h.UndoOf != nil { // ein Rückgängig wurde zurückgenommen: der ursprüngliche Eintrag gilt wieder
				if err := c.Q.SetUndone(c.Context, sqlc.SetUndoneParams{ID: *h.UndoOf, Undone: false}); err != nil {
					return HistoryUndoResult{}, err
				}
			}
			rcpt, err := originalRecipients(c, h)
			if err != nil {
				return HistoryUndoResult{}, err
			}
			if err := c.Emit("change.reverted", rcpt, ""); err != nil {
				return HistoryUndoResult{}, err
			}
			c.Affect("appointment", cur.ID, "Status "+curView.Status+" → "+target.Status)
			return HistoryUndoResult{HistoryID: newID.String()}, nil
		})
}

// originalRecipients: die Empfänger des ursprünglichen Ereignisses (sonst alle Mitglieder außer dem Aufrufer).
func originalRecipients(c *op.Ctx, h sqlc.History) ([]string, error) {
	if h.EventID == nil {
		return c.RecipientsExceptCaller(h.TeamID)
	}
	return c.Q.EventRecipients(c.Context, *h.EventID)
}
