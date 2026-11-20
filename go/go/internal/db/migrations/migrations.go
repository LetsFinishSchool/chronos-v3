// Package migrations bettet die SQL-Migrationen ein (goose).
package migrations

import (
	"context"
	"database/sql"
	"embed"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jackc/pgx/v5/stdlib"
	"github.com/pressly/goose/v3"
)

//go:embed *.sql
var files embed.FS

func provider(pool *pgxpool.Pool) (*goose.Provider, *sql.DB, error) {
	db := stdlib.OpenDBFromPool(pool)
	p, err := goose.NewProvider(goose.DialectPostgres, db, files)
	return p, db, err
}

// Up führt alle offenen Migrationen aus (Web beim Start). goose sperrt per Advisory-Lock nicht selbst;
// mehrere gleichzeitige Web-Instanzen sind im Spike nicht vorgesehen.
func Up(ctx context.Context, pool *pgxpool.Pool) error {
	p, db, err := provider(pool)
	if err != nil {
		return err
	}
	defer db.Close()
	_, err = p.Up(ctx)
	return err
}

// Latest ist die höchste eingebettete Version (der Worker wartet darauf).
func Latest(pool *pgxpool.Pool) (int64, error) {
	p, db, err := provider(pool)
	if err != nil {
		return 0, err
	}
	defer db.Close()
	var v int64
	for _, s := range p.ListSources() {
		v = max(v, s.Version)
	}
	return v, nil
}
