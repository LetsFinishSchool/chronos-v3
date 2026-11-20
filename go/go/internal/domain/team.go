// Package domain enthält die Fachbereiche Teams, Termine, Serien und Verlauf. Es kennt die Kanäle NICHT
// (Architekturregel V-1 §9, geprüft mit `make arch-check`).
package domain

import (
	"github.com/google/uuid"

	"chronos/internal/db/sqlc"
	"chronos/internal/op"
)

func Register(r *op.Registry) {
	registerTeams(r)
	registerAppointments(r)
	registerSeries(r)
	registerHistory(r)
}

type TeamCreateParams struct {
	Name     string  `json:"name" minLength:"1" maxLength:"100" doc:"Name des Teams"`
	ParentID *string `json:"parent_id,omitempty" format:"uuid" doc:"Eltern-Team; der Aufrufer muss dort Mitglied sein"`
}
type TeamCreateResult struct {
	TeamID string `json:"team_id"`
}

type TeamAddMemberParams struct {
	TeamID   string `json:"team_id" format:"uuid"`
	PersonID string `json:"person_id" minLength:"1" doc:"Keycloak-sub der Person (muss sich schon angemeldet haben)"`
}

type TeamIDParams struct {
	TeamID string `json:"team_id" format:"uuid"`
}
type Member struct {
	PersonID string `json:"person_id"`
	Name     string `json:"name"`
}
type EffectiveMembersResult struct {
	Members []Member `json:"members"`
}

type EffectiveTeamsParams struct {
	PersonID *string `json:"person_id,omitempty" doc:"Standard: der Aufrufer; andere Personen sind nicht erlaubt"`
}
type TeamRef struct {
	TeamID   string  `json:"team_id"`
	Name     string  `json:"name"`
	ParentID *string `json:"parent_id" nullable:"true"`
}
type EffectiveTeamsResult struct {
	Teams []TeamRef `json:"teams"`
}

func registerTeams(r *op.Registry) {
	op.Register(r, op.Op{Name: "team.create", Mutating: true,
		Description: "Legt ein Team an (optional unter einem Eltern-Team). Der Aufrufer wird direktes Mitglied."},
		func(c *op.Ctx, p TeamCreateParams) (TeamCreateResult, error) {
			var parent *uuid.UUID
			if p.ParentID != nil {
				id, err := op.ParseID(*p.ParentID, "parent_id")
				if err != nil {
					return TeamCreateResult{}, err
				}
				if err := c.RequireMember(id); err != nil {
					return TeamCreateResult{}, err
				}
				parent = &id
			}
			id := uuid.New()
			if err := c.Q.CreateTeam(c.Context, sqlc.CreateTeamParams{ID: id, Name: p.Name, ParentID: parent}); err != nil {
				return TeamCreateResult{}, err
			}
			if err := c.Q.AddTeamMember(c.Context, sqlc.AddTeamMemberParams{TeamID: id, PersonID: c.Caller.ID}); err != nil {
				return TeamCreateResult{}, err
			}
			c.Affect("team", id, "Team angelegt")
			return TeamCreateResult{TeamID: id.String()}, nil
		})

	op.Register(r, op.Op{Name: "team.add_member", Mutating: true,
		Description: "Fügt eine bereits bekannte Person als direktes Mitglied zu einem Team hinzu. Doppeltes Hinzufügen bleibt ohne Wirkung."},
		func(c *op.Ctx, p TeamAddMemberParams) (op.Empty, error) {
			id, err := op.ParseID(p.TeamID, "team_id")
			if err != nil {
				return op.Empty{}, err
			}
			if err := c.RequireMember(id); err != nil {
				return op.Empty{}, err
			}
			known, err := c.Q.PersonExists(c.Context, p.PersonID)
			if err != nil {
				return op.Empty{}, err
			}
			if !known {
				return op.Empty{}, op.NotFound("Person unbekannt")
			}
			if err := c.Q.AddTeamMember(c.Context, sqlc.AddTeamMemberParams{TeamID: id, PersonID: p.PersonID}); err != nil {
				return op.Empty{}, err
			}
			c.Affect("team", id, "Mitglied "+p.PersonID+" hinzugefügt")
			return op.Empty{}, nil
		})

	op.Register(r, op.Op{Name: "team.effective_members",
		Description: "Listet die effektiven Mitglieder eines Teams: direkte Mitglieder und die aller Unter-Teams, ohne Duplikate, nach person_id sortiert."},
		func(c *op.Ctx, p TeamIDParams) (EffectiveMembersResult, error) {
			id, err := op.ParseID(p.TeamID, "team_id")
			if err != nil {
				return EffectiveMembersResult{}, err
			}
			if err := c.RequireMember(id); err != nil {
				return EffectiveMembersResult{}, err
			}
			rows, err := c.Q.EffectiveMembers(c.Context, id)
			if err != nil {
				return EffectiveMembersResult{}, err
			}
			out := make([]Member, len(rows))
			for i, m := range rows {
				out[i] = Member{PersonID: m.PersonID, Name: m.Name}
			}
			return EffectiveMembersResult{Members: out}, nil
		})

	op.Register(r, op.Op{Name: "team.effective_teams",
		Description: "Listet alle Teams, in denen die Person direkt Mitglied ist, und alle übergeordneten Teams (nach Name, dann ID sortiert)."},
		func(c *op.Ctx, p EffectiveTeamsParams) (EffectiveTeamsResult, error) {
			who := c.Caller.ID
			if p.PersonID != nil && *p.PersonID != who {
				return EffectiveTeamsResult{}, op.Forbidden("nur die eigenen Teams sind abrufbar")
			}
			rows, err := c.Q.EffectiveTeams(c.Context, who)
			if err != nil {
				return EffectiveTeamsResult{}, err
			}
			out := make([]TeamRef, len(rows))
			for i, t := range rows {
				out[i] = TeamRef{TeamID: t.ID.String(), Name: t.Name}
				if t.ParentID != nil {
					s := t.ParentID.String()
					out[i].ParentID = &s
				}
			}
			return EffectiveTeamsResult{Teams: out}, nil
		})
}
