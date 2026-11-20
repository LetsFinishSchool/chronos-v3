package domain

import (
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/teambition/rrule-go"

	"chronos/internal/db/sqlc"
	"chronos/internal/op"
)

type SeriesCreateParams struct {
	TeamID          string   `json:"team_id" format:"uuid"`
	Title           string   `json:"title" minLength:"1" maxLength:"200"`
	RRule           string   `json:"rrule" minLength:"1" doc:"Wiederholungsregel nach RFC 5545 ohne Präfix RRULE:, z. B. FREQ=WEEKLY;BYDAY=MO"`
	DTStart         string   `json:"dtstart" pattern:"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$" doc:"Erster Termin in Ortszeit, z. B. 2026-03-02T18:00:00"`
	Timezone        string   `json:"timezone" minLength:"1" doc:"IANA-Zeitzone der Ortszeit"`
	DurationMinutes int      `json:"duration_minutes" minimum:"1" maximum:"1440"`
	Exdates         []string `json:"exdates,omitempty" doc:"Ausgenommene Vorkommen in Ortszeit, z. B. 2026-03-09T18:00:00"`
}
type SeriesCreateResult struct {
	SeriesID string `json:"series_id"`
}
type SeriesOccurrencesParams struct {
	SeriesID string `json:"series_id" format:"uuid"`
	From     string `json:"from" format:"date-time" doc:"Beginn des Fensters (eingeschlossen), UTC"`
	To       string `json:"to" format:"date-time" doc:"Ende des Fensters (ausgeschlossen), UTC"`
}
type Occurrence struct {
	StartsAt string `json:"starts_at"`
	EndsAt   string `json:"ends_at"`
}
type SeriesOccurrencesResult struct {
	Occurrences []Occurrence `json:"occurrences"`
}

type seriesView struct {
	ID              string   `json:"id"`
	TeamID          string   `json:"team_id"`
	Title           string   `json:"title"`
	RRule           string   `json:"rrule"`
	DTStart         string   `json:"dtstart"`
	Timezone        string   `json:"timezone"`
	DurationMinutes int      `json:"duration_minutes"`
	Exdates         []string `json:"exdates"`
}

const (
	localLayout    = "2006-01-02T15:04:05"
	maxOccurrences = 1000
	maxIterations  = 200000
)

func registerSeries(r *op.Registry) {
	op.Register(r, op.Op{Name: "series.create", Mutating: true,
		Description: "Legt eine Terminserie mit Wiederholungsregel (RRULE) an. Die Vorkommen werden bei Bedarf berechnet (Wanduhrzeit über Sommerzeitwechsel)."},
		func(c *op.Ctx, p SeriesCreateParams) (SeriesCreateResult, error) {
			team, err := op.ParseID(p.TeamID, "team_id")
			if err != nil {
				return SeriesCreateResult{}, err
			}
			ex := p.Exdates
			if ex == nil {
				ex = []string{}
			}
			s := sqlc.Series{ID: uuid.New(), TeamID: team, Title: p.Title, Rrule: p.RRule, Dtstart: p.DTStart, Timezone: p.Timezone,
				DurationMinutes: int32(p.DurationMinutes), Exdates: ex}
			if _, err := plan(s); err != nil { // Regel, Zeitzone und Ortszeiten prüfen
				return SeriesCreateResult{}, err
			}
			if err := c.RequireMember(team); err != nil {
				return SeriesCreateResult{}, err
			}
			if err := c.Q.CreateSeries(c.Context, sqlc.CreateSeriesParams(s)); err != nil {
				return SeriesCreateResult{}, err
			}
			if _, err := c.Record(op.HistoryInput{Action: "series.create", ObjectType: "series", ObjectID: s.ID, TeamID: team,
				After: seriesView{ID: s.ID.String(), TeamID: team.String(), Title: s.Title, RRule: s.Rrule, DTStart: s.Dtstart,
					Timezone: s.Timezone, DurationMinutes: p.DurationMinutes, Exdates: ex}}); err != nil {
				return SeriesCreateResult{}, err
			}
			c.Affect("series", s.ID, "Serie angelegt")
			return SeriesCreateResult{SeriesID: s.ID.String()}, nil
		})

	op.Register(r, op.Op{Name: "series.occurrences",
		Description: "Berechnet die Vorkommen einer Serie im Fenster [from, to) (höchstens 1000, nach Beginn sortiert, UTC)."},
		func(c *op.Ctx, p SeriesOccurrencesParams) (SeriesOccurrencesResult, error) {
			id, err := op.ParseID(p.SeriesID, "series_id")
			if err != nil {
				return SeriesOccurrencesResult{}, err
			}
			from, err := parseTS(p.From, "from")
			if err != nil {
				return SeriesOccurrencesResult{}, err
			}
			to, err := parseTS(p.To, "to")
			if err != nil {
				return SeriesOccurrencesResult{}, err
			}
			s, err := c.Q.GetSeries(c.Context, id)
			if err != nil {
				return SeriesOccurrencesResult{}, op.NotFoundIf(err, "Serie")
			}
			if err := c.RequireMember(s.TeamID); err != nil {
				return SeriesOccurrencesResult{}, err
			}
			pl, err := plan(s)
			if err != nil {
				return SeriesOccurrencesResult{}, err
			}
			return SeriesOccurrencesResult{Occurrences: pl.expand(from, to, time.Duration(s.DurationMinutes)*time.Minute)}, nil
		})
}

// EIGENBAU:BEGIN Wanduhr-Ausdehnung der RRULE: rrule-go rechnet auf "schwebender" Ortszeit (als UTC beschriftet),
// Sommerzeit, UNTIL (UTC), EXDATE (Ortszeit), Fenster und Obergrenze setzt dieser Block um (rrule-go kennt keine Zeitzonen-Wanduhr).
type seriesPlan struct {
	rule *rrule.RRule
	loc  *time.Location
	ex   map[time.Time]bool
}

var untilRe = regexp.MustCompile(`(?i)(?:^|;)UNTIL=([0-9T]+)(Z?)(?:;|$)`)

func plan(s sqlc.Series) (*seriesPlan, error) {
	loc, err := time.LoadLocation(s.Timezone)
	if err != nil {
		return nil, op.Validation("timezone ist kein IANA-Name")
	}
	start, err := time.ParseInLocation(localLayout, s.Dtstart, time.UTC)
	if err != nil {
		return nil, op.Validation("dtstart ist keine Ortszeit (YYYY-MM-DDTHH:MM:SS)")
	}
	ex := map[time.Time]bool{}
	for _, e := range s.Exdates {
		t, err := time.ParseInLocation(localLayout, e, time.UTC)
		if err != nil {
			return nil, op.Validation("exdates enthält keine Ortszeit: %s", e)
		}
		ex[t] = true
	}
	text := strings.TrimSpace(s.Rrule)
	if strings.Contains(strings.ToUpper(text), "RRULE:") || strings.ContainsAny(text, "\n\r") {
		return nil, op.InvalidRRule("rrule ohne Präfix RRULE: angeben")
	}
	opt, err := rrule.StrToROption(text)
	if err != nil {
		return nil, op.InvalidRRule("%v", err)
	}
	up := strings.ToUpper(text)
	if !strings.HasPrefix(up, "FREQ=") && !strings.Contains(up, ";FREQ=") {
		return nil, op.InvalidRRule("FREQ fehlt")
	}
	if opt.Count > 0 && !opt.Until.IsZero() {
		return nil, op.InvalidRRule("COUNT und UNTIL schließen sich aus")
	}
	if iv := regexp.MustCompile(`(?i)(?:^|;)INTERVAL=(-?[0-9]+)`).FindStringSubmatch(text); iv != nil {
		if n, _ := strconv.Atoi(iv[1]); n < 1 {
			return nil, op.InvalidRRule("INTERVAL muss mindestens 1 sein")
		}
	}
	for _, d := range opt.Bymonthday {
		if d == 0 {
			return nil, op.InvalidRRule("BYMONTHDAY darf nicht 0 sein")
		}
	}
	opt.Dtstart = start
	if !opt.Until.IsZero() {
		if m := untilRe.FindStringSubmatch(text); m != nil && m[2] != "" { // UNTIL mit Z ist ein UTC-Zeitpunkt
			opt.Until = wall(opt.Until.In(loc))
		}
	}
	rule, err := rrule.NewRRule(*opt)
	if err != nil {
		return nil, op.InvalidRRule("%v", err)
	}
	return &seriesPlan{rule: rule, loc: loc, ex: ex}, nil
}

func wall(t time.Time) time.Time {
	return time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), 0, time.UTC)
}

func (p *seriesPlan) expand(from, to time.Time, dur time.Duration) []Occurrence {
	out := []Occurrence{}
	next := p.rule.Iterator()
	for i := 0; i < maxIterations && len(out) < maxOccurrences; i++ {
		w, ok := next()
		if !ok {
			break
		}
		if p.ex[w] {
			continue
		}
		st := time.Date(w.Year(), w.Month(), w.Day(), w.Hour(), w.Minute(), w.Second(), 0, p.loc).UTC()
		if !st.Before(to) {
			break
		}
		if st.Before(from) {
			continue
		}
		out = append(out, Occurrence{StartsAt: st.Format(tsLayout), EndsAt: st.Add(dur).Format(tsLayout)})
	}
	return out
}

// EIGENBAU:END
