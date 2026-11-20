// Chronos-Spike (Go): ein Programm, zwei Startarten: `web` und `worker`.
package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/danielgtaylor/huma/v2"
	"github.com/danielgtaylor/huma/v2/adapters/humachi"
	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	_ "time/tzdata"

	"chronos/internal/ai"
	"chronos/internal/auth"
	"chronos/internal/config"
	"chronos/internal/db/migrations"
	"chronos/internal/domain"
	"chronos/internal/logx"
	"chronos/internal/notify"
	"chronos/internal/op"
	"chronos/internal/worker"
)

func main() {
	logx.Setup()
	if len(os.Args) < 2 || (os.Args[1] != "web" && os.Args[1] != "worker") {
		slog.Error("Aufruf: chronos web|worker")
		os.Exit(2)
	}
	cfg := config.Load()
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	pool, err := connect(ctx, cfg.DatabaseURL)
	if err != nil {
		slog.Error("Datenbank nicht erreichbar", "error", err.Error())
		os.Exit(1)
	}
	defer pool.Close()

	switch os.Args[1] {
	case "web":
		err = runWeb(ctx, &cfg, pool)
	case "worker":
		err = runWorker(ctx, &cfg, pool)
	}
	if err != nil && !errors.Is(err, context.Canceled) && !errors.Is(err, http.ErrServerClosed) {
		slog.Error("beendet mit Fehler", "error", err.Error())
		os.Exit(1)
	}
}

func connect(ctx context.Context, url string) (*pgxpool.Pool, error) {
	pc, err := pgxpool.ParseConfig(url)
	if err != nil {
		return nil, err
	}
	pc.MaxConns = 12
	var pool *pgxpool.Pool
	for i := 0; i < 60; i++ { // die Datenbank darf kurz nach dem Start noch fehlen
		if pool, err = pgxpool.NewWithConfig(ctx, pc); err == nil {
			if err = pool.Ping(ctx); err == nil {
				return pool, nil
			}
			pool.Close()
		}
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(time.Second):
		}
	}
	return nil, err
}

func runWeb(ctx context.Context, cfg *config.Config, pool *pgxpool.Pool) error {
	if err := migrations.Up(ctx, pool); err != nil {
		return err
	}
	op.InstallHumaErrors()
	router := chi.NewRouter()
	router.Use(op.Base(cfg.Faults))
	router.NotFound(func(w http.ResponseWriter, _ *http.Request) { op.WriteError(w, op.NotFound("nicht gefunden")) })
	router.MethodNotAllowed(func(w http.ResponseWriter, _ *http.Request) {
		op.WriteError(w, &op.Error{Status: 405, Code: "validation_error", Message: "Methode nicht erlaubt"})
	})

	router.Get("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if err := pool.Ping(r.Context()); err != nil {
			op.WriteJSON(w, 503, map[string]string{"status": "unavailable"})
			return
		}
		op.WriteJSON(w, 200, map[string]string{"status": "ok"})
	})
	if cfg.StaticDir != "" {
		router.Handle("/static/*", http.StripPrefix("/static/", http.FileServer(http.Dir(cfg.StaticDir))))
	}

	a := auth.New(cfg, pool)
	a.Mount(router)

	// Operationen: alle hinter der Bearer-Prüfung, genau eine Beschreibung je Operation.
	var reg *op.Registry
	router.Group(func(g chi.Router) {
		g.Use(a.Middleware(false))
		hc := huma.DefaultConfig("Chronos", "spike")
		hc.DocsPath = ""
		hc.CreateHooks = nil
		hc.Components.Schemas = huma.NewMapRegistry("#/components/schemas/", op.SchemaNamer)
		api := humachi.New(g, hc)
		reg = op.NewRegistry(api, pool, cfg)
		domain.Register(reg)
		notify.Register(reg)
		ai.Register(reg)
	})
	reg.Mount(router)

	srv := &http.Server{Addr: ":" + cfg.Port, Handler: router, ReadHeaderTimeout: 10 * time.Second}
	go func() {
		<-ctx.Done()
		sctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = srv.Shutdown(sctx)
	}()
	slog.Info("Web gestartet", "port", cfg.Port)
	return srv.ListenAndServe()
}

func runWorker(ctx context.Context, cfg *config.Config, pool *pgxpool.Pool) error {
	want, err := migrations.Latest(pool)
	if err != nil {
		return err
	}
	hs := &http.Server{Addr: ":" + cfg.WorkerHealthPort, Handler: worker.Health(pool), ReadHeaderTimeout: 10 * time.Second}
	go func() { _ = hs.ListenAndServe() }()
	defer hs.Close()
	if err := worker.WaitForSchema(ctx, pool, want); err != nil {
		return err
	}
	return worker.New(pool, cfg).Run(ctx)
}
