package domain

import (
	"testing"
	"time"

	"chronos/internal/db/sqlc"
)

func occ(t *testing.T, rule, dtstart string, ex []string, from, to string) []Occurrence {
	t.Helper()
	p, err := plan(sqlc.Series{Rrule: rule, Dtstart: dtstart, Timezone: "Europe/Berlin", Exdates: ex})
	if err != nil {
		t.Fatal(err)
	}
	f, _ := time.Parse(time.RFC3339, from)
	e, _ := time.Parse(time.RFC3339, to)
	return p.expand(f, e, time.Hour)
}

func TestWallClockAcrossDST(t *testing.T) {
	got := occ(t, "FREQ=WEEKLY;BYDAY=MO;COUNT=8", "2026-03-02T18:00:00", nil, "2026-01-01T00:00:00Z", "2030-01-01T00:00:00Z")
	if len(got) != 8 || got[3].StartsAt != "2026-03-23T17:00:00Z" || got[4].StartsAt != "2026-03-30T16:00:00Z" {
		t.Fatalf("Sommerzeit falsch behandelt: %v", got)
	}
}

func TestUntilIsUTCInstantAndExdate(t *testing.T) {
	got := occ(t, "FREQ=DAILY;UNTIL=20260310T170000Z", "2026-03-05T18:00:00", []string{"2026-03-07T18:00:00"}, "2026-01-01T00:00:00Z", "2030-01-01T00:00:00Z")
	if len(got) != 5 || got[len(got)-1].StartsAt != "2026-03-10T17:00:00Z" {
		t.Fatalf("UNTIL/EXDATE falsch: %v", got)
	}
}

func TestInvalidRules(t *testing.T) {
	for _, r := range []string{"FREQ=FOO", "FREQ=WEEKLY;BYDAY=XX", "FREQ=WEEKLY;COUNT=3;UNTIL=20270101T000000Z",
		"FREQ=MONTHLY;BYMONTHDAY=0", "FREQ=DAILY;INTERVAL=0", "INTERVAL=2;COUNT=3", "RRULE:FREQ=DAILY"} {
		if _, err := plan(sqlc.Series{Rrule: r, Dtstart: "2026-03-02T18:00:00", Timezone: "Europe/Berlin"}); err == nil {
			t.Errorf("%q wurde angenommen", r)
		}
	}
}

func TestLimit(t *testing.T) {
	if got := occ(t, "FREQ=DAILY", "2026-01-01T08:00:00", nil, "2026-01-01T00:00:00Z", "2031-01-01T00:00:00Z"); len(got) != 1000 {
		t.Fatalf("Obergrenze: %d", len(got))
	}
}
