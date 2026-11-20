package domain

import (
	"time"

	"github.com/google/uuid"

	"chronos/internal/db/sqlc"
	"chronos/internal/op"
)

const (
	statusPlanned   = "geplant"
	statusCancelled = "abgesagt"
	statusDeleted   = "gelöscht"
	tsLayout        = "2006-01-02T15:04:05Z"
)

// AppointmentView ist die Außensicht und zugleich das Zustandsabbild in Verlauf (before/after).
type AppointmentView struct {
	ID       string `json:"id"`
	TeamID   string `json:"team_id"`
	Title    string `json:"title"`
	StartsAt string `json:"starts_at"`
	EndsAt   string `json:"ends_at"`
	Timezone string `json:"timezone"`
	Status   string `json:"status" enum:"geplant,abgesagt,gelöscht"`
}

func viewOf(a sqlc.Appointment) AppointmentView {
	return AppointmentView{ID: a.ID.String(), TeamID: a.TeamID.String(), Title: a.Title, StartsAt: a.StartsAt.UTC().Format(tsLayout),
		EndsAt: a.EndsAt.UTC().Format(tsLayout), Timezone: a.Timezone, Status: a.Status}
}

func parseTS(s, what string) (time.Time, error) {
	t, err := time.Parse(time.RFC3339, s)
	if err != nil {
		return t, op.Validation("%s ist kein Zeitpunkt (ISO 8601)", what)
	}
	return t.UTC(), nil
}

type AppointmentCreateParams struct {
	TeamID   string `json:"team_id" format:"uuid"`
	Title    string `json:"title" minLength:"1" maxLength:"200"`
	StartsAt string `json:"starts_at" format:"date-time" doc:"Beginn, UTC, z. B. 2026-12-01T17:00:00Z"`
	EndsAt   string `json:"ends_at" format:"date-time" doc:"Ende, UTC, nach dem Beginn"`
	Timezone string `json:"timezone" minLength:"1" doc:"IANA-Zeitzone, z. B. Europe/Berlin"`
}
type AppointmentCreateResult struct {
	AppointmentID string `json:"appointment_id"`
}
type AppointmentIDParams struct {
	AppointmentID string `json:"appointment_id" format:"uuid"`
}
type AppointmentGetResult struct {
	Appointment AppointmentView `json:"appointment"`
}
type AppointmentListResult struct {
	Appointments []AppointmentView `json:"appointments"`
}

// loadVisible lädt einen (nicht gelöschten) Termin und prüft die Mitgliedschaft im Team.
func loadVisible(c *op.Ctx, idStr string) (sqlc.Appointment, error) {
	id, err := op.ParseID(idStr, "appointment_id")
	if err != nil {
		return sqlc.Appointment{}, err
	}
	a, err := c.Q.GetAppointment(c.Context, id)
	if err != nil {
		return a, op.NotFoundIf(err, "Termin")
	}
	if a.Status == statusDeleted {
		return a, op.NotFound("Termin nicht gefunden")
	}
	return a, c.RequireMember(a.TeamID)
}

func registerAppointments(r *op.Registry) {
	registerReschedule(r)
	op.Register(r, op.Op{Name: "appointment.create", Mutating: true,
		Description: "Legt einen Termin im Team an (Status geplant). Die übrigen Teammitglieder werden benachrichtigt."},
		func(c *op.Ctx, p AppointmentCreateParams) (AppointmentCreateResult, error) {
			team, err := op.ParseID(p.TeamID, "team_id")
			if err != nil {
				return AppointmentCreateResult{}, err
			}
			starts, err := parseTS(p.StartsAt, "starts_at")
			if err != nil {
				return AppointmentCreateResult{}, err
			}
			ends, err := parseTS(p.EndsAt, "ends_at")
			if err != nil {
				return AppointmentCreateResult{}, err
			}
			if !ends.After(starts) {
				return AppointmentCreateResult{}, op.Validation("ends_at muss nach starts_at liegen")
			}
			if _, err := time.LoadLocation(p.Timezone); err != nil {
				return AppointmentCreateResult{}, op.Validation("timezone ist kein IANA-Name")
			}
			if err := c.RequireMember(team); err != nil {
				return AppointmentCreateResult{}, err
			}
			a := sqlc.Appointment{ID: uuid.New(), TeamID: team, Title: p.Title, StartsAt: starts, EndsAt: ends, Timezone: p.Timezone, Status: statusPlanned}
			if err := c.Q.CreateAppointment(c.Context, sqlc.CreateAppointmentParams(a)); err != nil {
				return AppointmentCreateResult{}, err
			}
			if err := recordAndEmit(c, "appointment.create", "appointment.created", team, a.ID, nil, viewOf(a)); err != nil {
				return AppointmentCreateResult{}, err
			}
			c.Affect("appointment", a.ID, "Termin angelegt")
			return AppointmentCreateResult{AppointmentID: a.ID.String()}, nil
		})

	op.Register(r, op.Op{Name: "appointment.get",
		Description: "Liest einen Termin (gelöschte Termine sind nicht abrufbar)."},
		func(c *op.Ctx, p AppointmentIDParams) (AppointmentGetResult, error) {
			a, err := loadVisible(c, p.AppointmentID)
			if err != nil {
				return AppointmentGetResult{}, err
			}
			return AppointmentGetResult{Appointment: viewOf(a)}, nil
		})

	op.Register(r, op.Op{Name: "appointment.list",
		Description: "Listet die Termine eines Teams (auch abgesagte, keine gelöschten) nach Beginn sortiert."},
		func(c *op.Ctx, p TeamIDParams) (AppointmentListResult, error) {
			team, err := op.ParseID(p.TeamID, "team_id")
			if err != nil {
				return AppointmentListResult{}, err
			}
			if err := c.RequireMember(team); err != nil {
				return AppointmentListResult{}, err
			}
			rows, err := c.Q.ListAppointments(c.Context, team)
			if err != nil {
				return AppointmentListResult{}, err
			}
			out := make([]AppointmentView, len(rows))
			for i, a := range rows {
				out[i] = viewOf(a)
			}
			return AppointmentListResult{Appointments: out}, nil
		})

	op.Register(r, op.Op{Name: "appointment.cancel", Mutating: true,
		Description: "Sagt einen geplanten Termin ab. Die übrigen Teammitglieder werden benachrichtigt."},
		func(c *op.Ctx, p AppointmentIDParams) (op.Empty, error) {
			a, err := loadVisible(c, p.AppointmentID)
			if err != nil {
				return op.Empty{}, err
			}
			if a.Status != statusPlanned {
				return op.Empty{}, op.Conflict("Termin ist nicht geplant")
			}
			before := viewOf(a)
			a.Status = statusCancelled
			if err := store(c, a); err != nil {
				return op.Empty{}, err
			}
			if err := recordAndEmit(c, "appointment.cancel", "appointment.cancelled", a.TeamID, a.ID, before, viewOf(a)); err != nil {
				return op.Empty{}, err
			}
			c.Affect("appointment", a.ID, "Status geplant → abgesagt")
			return op.Empty{}, nil
		})
}

type AppointmentRescheduleParams struct {
	AppointmentID string `json:"appointment_id" format:"uuid"`
	StartsAt      string `json:"starts_at" format:"date-time" doc:"Neuer Beginn, UTC"`
	EndsAt        string `json:"ends_at" format:"date-time" doc:"Neues Ende, UTC, nach dem Beginn"`
}

func registerReschedule(r *op.Registry) {
	op.Register(r, op.Op{Name: "appointment.reschedule", Mutating: true,
		Description: "Verschiebt einen geplanten Termin auf einen neuen Zeitraum. Die übrigen Teammitglieder werden benachrichtigt."},
		func(c *op.Ctx, p AppointmentRescheduleParams) (op.Empty, error) {
			starts, err := parseTS(p.StartsAt, "starts_at")
			if err != nil {
				return op.Empty{}, err
			}
			ends, err := parseTS(p.EndsAt, "ends_at")
			if err != nil {
				return op.Empty{}, err
			}
			if !ends.After(starts) {
				return op.Empty{}, op.Validation("ends_at muss nach starts_at liegen")
			}
			a, err := loadVisible(c, p.AppointmentID)
			if err != nil {
				return op.Empty{}, err
			}
			if a.Status != statusPlanned {
				return op.Empty{}, op.Conflict("Termin ist nicht geplant")
			}
			before := viewOf(a)
			a.StartsAt, a.EndsAt = starts, ends
			if err := store(c, a); err != nil {
				return op.Empty{}, err
			}
			if err := recordAndEmit(c, "appointment.reschedule", "appointment.rescheduled", a.TeamID, a.ID, before, viewOf(a)); err != nil {
				return op.Empty{}, err
			}
			c.Affect("appointment", a.ID, "Zeitraum "+before.StartsAt+" → "+p.StartsAt)
			return op.Empty{}, nil
		})
}

func store(c *op.Ctx, a sqlc.Appointment) error {
	return c.Q.RestoreAppointment(c.Context, sqlc.RestoreAppointmentParams{ID: a.ID, Title: a.Title, StartsAt: a.StartsAt,
		EndsAt: a.EndsAt, Timezone: a.Timezone, Status: a.Status})
}

// recordAndEmit schreibt Verlaufseintrag und Ereignis (Empfänger: alle effektiven Mitglieder außer dem Aufrufer).
func recordAndEmit(c *op.Ctx, action, eventType string, team, obj uuid.UUID, before, after any) error {
	if _, err := c.Record(op.HistoryInput{Action: action, ObjectType: "appointment", ObjectID: obj, TeamID: team,
		Before: before, After: after, WithEvent: true}); err != nil {
		return err
	}
	rcpt, err := c.RecipientsExceptCaller(team)
	if err != nil {
		return err
	}
	return c.Emit(eventType, rcpt, "")
}
