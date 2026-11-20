// Package logx: JSON-Logzeilen mit ts, level, msg, correlation_id (und event_id) nach V-1 §3.
package logx

import (
	"context"
	"log/slog"
	"os"
	"strings"
	"time"
)

type key int

const (
	corrKey key = iota
	eventKey
)

func WithCorrelation(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, corrKey, id)
}

func WithEvent(ctx context.Context, id string) context.Context {
	return context.WithValue(ctx, eventKey, id)
}

func Correlation(ctx context.Context) string {
	s, _ := ctx.Value(corrKey).(string)
	return s
}

type ctxHandler struct{ slog.Handler }

func (h ctxHandler) Handle(ctx context.Context, r slog.Record) error {
	r.AddAttrs(slog.String("correlation_id", Correlation(ctx)))
	if ev, ok := ctx.Value(eventKey).(string); ok {
		r.AddAttrs(slog.String("event_id", ev))
	}
	return h.Handler.Handle(ctx, r)
}

func (h ctxHandler) WithAttrs(a []slog.Attr) slog.Handler { return ctxHandler{h.Handler.WithAttrs(a)} }
func (h ctxHandler) WithGroup(n string) slog.Handler      { return ctxHandler{h.Handler.WithGroup(n)} }

// Setup richtet den Standard-Logger ein (immer JSON, `LOG_FORMAT=json` ist der einzige Wert).
func Setup() {
	opts := &slog.HandlerOptions{ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
		if len(groups) > 0 {
			return a
		}
		switch a.Key {
		case slog.TimeKey:
			return slog.String("ts", a.Value.Time().UTC().Format(time.RFC3339Nano))
		case slog.LevelKey:
			return slog.String("level", strings.ToLower(a.Value.String()))
		}
		return a
	}}
	slog.SetDefault(slog.New(ctxHandler{slog.NewJSONHandler(os.Stdout, opts)}))
}
