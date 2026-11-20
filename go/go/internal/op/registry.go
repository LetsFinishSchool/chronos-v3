// Package op enthält die EINE Operationsbeschreibung (V-1 §4). Jede Operation wird mit Register genau einmal
// beschrieben: Name, Beschreibung, lesend/schreibend sowie Parameter- und Ergebnistyp (Go-Strukturen mit Tags).
// Daraus entstehen Validierung (huma), Endpunkt, GET /api/v1/operations, KI-Werkzeugschema und Brückentypen.
package op

import (
	"context"
	"encoding/json"
	"log/slog"
	"net/http"
	"reflect"
	"sort"
	"strings"
	"sync"

	"github.com/danielgtaylor/huma/v2"
	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"chronos/internal/config"
	"chronos/internal/db/sqlc"
	"chronos/internal/logx"
)

// Op ist die Beschreibung einer Operation. Mehr muss ein Entwickler nicht angeben.
type Op struct {
	Name        string
	Description string
	Mutating    bool
}

// Descriptor ist die abgeleitete, serialisierbare Beschreibung (Antwort von GET /api/v1/operations).
type Descriptor struct {
	Name             string         `json:"name"`
	Description      string         `json:"description"`
	Mutating         bool           `json:"mutating"`
	PreviewSupported bool           `json:"preview_supported"`
	ParamsSchema     map[string]any `json:"params_schema"`
	ResultSchema     map[string]any `json:"result_schema"`
}

type Registry struct {
	API  huma.API
	Pool *pgxpool.Pool
	Cfg  *config.Config

	mu    sync.Mutex
	descs map[string]*Descriptor
}

func NewRegistry(api huma.API, pool *pgxpool.Pool, cfg *config.Config) *Registry {
	return &Registry{API: api, Pool: pool, Cfg: cfg, descs: map[string]*Descriptor{}}
}

type requestBody[P any] struct {
	Params  P    `json:"params" doc:"Parameter der Operation"`
	Preview bool `json:"preview,omitempty" doc:"Nur Vorschau ohne Schreibwirkung (schreibende Operationen)"`
}
type request[P any] struct{ Body requestBody[P] }

// PreviewResult ist die Antwort einer Vorschau.
type PreviewResult struct {
	Count    int        `json:"count"`
	Affected []Affected `json:"affected"`
}
type responseBody[R any] struct {
	Result  *R             `json:"result,omitempty"`
	Preview *PreviewResult `json:"preview,omitempty"`
}
type response[R any] struct{ Body responseBody[R] }

// Register beschreibt eine Operation und hängt ihren Endpunkt ein. P und R sind die Parameter- und Ergebnistypen.
func Register[P, R any](r *Registry, o Op, h func(c *Ctx, p P) (R, error)) {
	d := &Descriptor{
		Name: o.Name, Description: o.Description, Mutating: o.Mutating, PreviewSupported: o.Mutating,
		ParamsSchema: r.inlineSchema(reflect.TypeFor[P](), "Params"),
		ResultSchema: r.inlineSchema(reflect.TypeFor[R](), "Result"),
	}
	r.mu.Lock()
	r.descs[o.Name] = d
	r.mu.Unlock()

	huma.Register(r.API, huma.Operation{
		OperationID: o.Name,
		Method:      http.MethodPost,
		Path:        "/api/v1/operations/" + o.Name,
		Summary:     o.Description,
		Tags:        []string{"operations"},
	}, func(ctx context.Context, in *request[P]) (*response[R], error) {
		var result R
		pv, err := r.execute(ctx, o, in.Body.Preview, func(c *Ctx) error {
			var e error
			result, e = h(c, in.Body.Params)
			return e
		})
		if err != nil {
			return nil, err
		}
		if pv != nil {
			return &response[R]{Body: responseBody[R]{Preview: pv}}, nil
		}
		return &response[R]{Body: responseBody[R]{Result: &result}}, nil
	})
}

// execute führt die Operation aus: schreibend in einer Transaktion (Vorschau = zurückrollen), lesend direkt.
func (r *Registry) execute(ctx context.Context, o Op, preview bool, run func(c *Ctx) error) (*PreviewResult, error) {
	caller, ok := CallerFrom(ctx)
	if !ok {
		return nil, Unauthenticated("Anmeldung erforderlich")
	}
	c := &Ctx{
		Context: ctx, Pool: r.Pool, Cfg: r.Cfg, Caller: caller, CorrelationID: logx.Correlation(ctx), OpName: o.Name,
		BundleID: uuid.New(), EventID: uuid.New(), Q: sqlc.New(r.Pool),
	}
	if r.Cfg.Faults {
		c.fault, _ = ctx.Value(faultKey{}).(string)
	}
	if !o.Mutating {
		return nil, wrap(ctx, o.Name, run(c))
	}
	tx, err := r.Pool.BeginTx(ctx, pgx.TxOptions{})
	if err != nil {
		return nil, wrap(ctx, o.Name, err)
	}
	defer tx.Rollback(context.WithoutCancel(ctx)) //nolint:errcheck
	c.Q = sqlc.New(tx)
	if err := run(c); err != nil {
		return nil, wrap(ctx, o.Name, err)
	}
	if preview {
		aff := c.affected
		if aff == nil {
			aff = []Affected{}
		}
		return &PreviewResult{Count: len(aff), Affected: aff}, nil // Rollback über defer: keine Schreibwirkung
	}
	if err := tx.Commit(ctx); err != nil {
		return nil, wrap(ctx, o.Name, err)
	}
	return nil, nil
}

func wrap(ctx context.Context, name string, err error) error {
	if err == nil {
		return nil
	}
	if e, ok := err.(*Error); ok {
		return e
	}
	slog.ErrorContext(ctx, "Operation fehlgeschlagen", "operation", name, "error", err.Error())
	return Internal("interner Fehler")
}

// Descriptors liefert alle Beschreibungen nach Name sortiert.
func (r *Registry) Descriptors() []*Descriptor {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]*Descriptor, 0, len(r.descs))
	for _, d := range r.descs {
		out = append(out, d)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
	return out
}

// ToolName wandelt einen Operationsnamen in einen KI-Werkzeugnamen (appointment.create → appointment_create).
func ToolName(op string) string { return strings.ReplaceAll(op, ".", "_") }

// Tool ist eine Anthropic-Werkzeugdefinition.
type Tool struct {
	Name        string         `json:"name"`
	Description string         `json:"description"`
	InputSchema map[string]any `json:"input_schema"`
}

// Tools leitet die KI-Werkzeuge aus den Operationsbeschreibungen ab.
func (r *Registry) Tools() []Tool {
	ds := r.Descriptors()
	out := make([]Tool, len(ds))
	for i, d := range ds {
		out[i] = Tool{Name: ToolName(d.Name), Description: d.Description, InputSchema: d.ParamsSchema}
	}
	return out
}

// OperationName findet den Operationsnamen zu einem Werkzeugnamen.
func (r *Registry) OperationName(tool string) (string, bool) {
	for _, d := range r.Descriptors() {
		if ToolName(d.Name) == tool {
			return d.Name, true
		}
	}
	return "", false
}

// EIGENBAU:BEGIN huma-Schema ohne $ref auflösen (JSON Schema je Operation muss in sich geschlossen sein)
func (r *Registry) inlineSchema(t reflect.Type, hint string) map[string]any {
	reg := r.API.OpenAPI().Components.Schemas
	s := reg.Schema(t, false, hint)
	var m map[string]any
	b, err := json.Marshal(s)
	if err == nil {
		err = json.Unmarshal(b, &m)
	}
	if err != nil {
		panic(err)
	}
	return r.deref(m, 0).(map[string]any)
}

func (r *Registry) deref(v any, depth int) any {
	if depth > 32 {
		panic("Schema zu tief verschachtelt oder rekursiv")
	}
	switch x := v.(type) {
	case map[string]any:
		if ref, ok := x["$ref"].(string); ok {
			target, err := json.Marshal(r.API.OpenAPI().Components.Schemas.SchemaFromRef(ref))
			if err != nil {
				panic(err)
			}
			var m map[string]any
			if err := json.Unmarshal(target, &m); err != nil {
				panic(err)
			}
			return r.deref(m, depth+1)
		}
		for k, vv := range x {
			x[k] = r.deref(vv, depth+1)
		}
		return x
	case []any:
		for i := range x {
			x[i] = r.deref(x[i], depth+1)
		}
		return x
	}
	return v
}

// EIGENBAU:END
