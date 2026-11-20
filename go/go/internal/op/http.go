package op

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"

	"chronos/internal/logx"
)

// Mount hängt die abgeleiteten, unauthentifizierten Listen ein.
func (r *Registry) Mount(mux chi.Router) {
	mux.Get("/api/v1/operations", func(w http.ResponseWriter, _ *http.Request) {
		WriteJSON(w, 200, map[string]any{"operations": r.Descriptors()})
	})
	mux.Get("/api/v1/ai/tools", func(w http.ResponseWriter, _ *http.Request) {
		WriteJSON(w, 200, map[string]any{"tools": r.Tools()})
	})
}

func WriteJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func WriteError(w http.ResponseWriter, e *Error) { WriteJSON(w, e.Status, e) }

type statusWriter struct {
	http.ResponseWriter
	status int
}

func (s *statusWriter) WriteHeader(c int) { s.status = c; s.ResponseWriter.WriteHeader(c) }

// Base ist die äußerste Middleware: Korrelations-ID, Fehlerinjektions-Header, Panikschutz und Zugriffslog.
func Base(faults bool) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			id := req.Header.Get("X-Correlation-Id")
			if id == "" || len(id) > 64 {
				b := make([]byte, 8)
				_, _ = rand.Read(b)
				id = hex.EncodeToString(b)
			}
			w.Header().Set("X-Correlation-Id", id)
			ctx := logx.WithCorrelation(req.Context(), id)
			if faults {
				if f := req.Header.Get("X-Spike-Fault"); f != "" {
					ctx = WithFault(ctx, f)
				}
			}
			req = req.WithContext(ctx)
			sw := &statusWriter{ResponseWriter: w, status: 200}
			start := time.Now()
			defer func() {
				if rec := recover(); rec != nil {
					slog.ErrorContext(ctx, "Panik im Handler", "panic", rec)
					if sw.status == 200 {
						WriteError(sw, Internal("interner Fehler"))
					}
				}
				if req.URL.Path != "/healthz" {
					slog.InfoContext(ctx, "request", "method", req.Method, "path", req.URL.Path, "status", sw.status,
						"duration_ms", time.Since(start).Milliseconds())
				}
			}()
			next.ServeHTTP(sw, req)
		})
	}
}
