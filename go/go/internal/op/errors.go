package op

import (
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"path"
	"reflect"
	"strings"

	"github.com/danielgtaylor/huma/v2"
	"github.com/jackc/pgx/v5"
)

// Error ist der einzige Fehlertyp der API (V-1 §3): {"error":{"code","message"}}.
type Error struct {
	Status  int
	Code    string
	Message string
}

func (e *Error) Error() string  { return e.Code + ": " + e.Message }
func (e *Error) GetStatus() int { return e.Status }

func (e *Error) MarshalJSON() ([]byte, error) {
	return json.Marshal(map[string]any{"error": map[string]string{"code": e.Code, "message": e.Message}})
}

func newErr(status int, code, format string, args ...any) *Error {
	return &Error{Status: status, Code: code, Message: fmt.Sprintf(format, args...)}
}

func Unauthenticated(f string, a ...any) *Error { return newErr(401, "unauthenticated", f, a...) }
func Forbidden(f string, a ...any) *Error       { return newErr(403, "forbidden", f, a...) }
func NotFound(f string, a ...any) *Error        { return newErr(404, "not_found", f, a...) }
func Validation(f string, a ...any) *Error      { return newErr(422, "validation_error", f, a...) }
func InvalidRRule(f string, a ...any) *Error    { return newErr(422, "invalid_rrule", f, a...) }
func Conflict(f string, a ...any) *Error        { return newErr(409, "conflict", f, a...) }
func NotUndoable(f string, a ...any) *Error     { return newErr(409, "not_undoable", f, a...) }
func Provider(f string, a ...any) *Error        { return newErr(502, "provider_error", f, a...) }
func Internal(f string, a ...any) *Error        { return newErr(500, "internal", f, a...) }

// NotFoundIf übersetzt "keine Zeile" in 404; andere Fehler bleiben unverändert.
func NotFoundIf(err error, what string) error {
	if errors.Is(err, pgx.ErrNoRows) {
		return NotFound("%s nicht gefunden", what)
	}
	return err
}

var codeForStatus = map[int]string{
	401: "unauthenticated", 403: "forbidden", 404: "not_found", 405: "validation_error", 409: "conflict",
	422: "validation_error", 500: "internal", 502: "provider_error",
}

// InstallHumaErrors lenkt alle Fehler, die huma selbst erzeugt (Validierung, Syntax), in das Fehlerformat um.
func InstallHumaErrors() {
	huma.DefaultArrayNullable = false
	huma.NewError = func(status int, msg string, errs ...error) huma.StatusError {
		if status == http.StatusBadRequest || status == http.StatusRequestEntityTooLarge || status == http.StatusUnsupportedMediaType {
			status = http.StatusUnprocessableEntity
		}
		code, ok := codeForStatus[status]
		if !ok {
			code = "internal"
		}
		parts := []string{msg}
		for _, e := range errs {
			if d, ok := e.(*huma.ErrorDetail); ok {
				parts = append(parts, fmt.Sprintf("%s (%s)", d.Message, d.Location))
			} else if e != nil {
				parts = append(parts, e.Error())
			}
		}
		return &Error{Status: status, Code: code, Message: strings.Join(parts, "; ")}
	}
}

// SchemaNamer macht Schemanamen über Pakete hinweg eindeutig (gleiche Typnamen in mehreren Paketen).
func SchemaNamer(t reflect.Type, hint string) string {
	name := huma.DefaultSchemaNamer(t, hint)
	for t.Kind() == reflect.Pointer || t.Kind() == reflect.Slice {
		t = t.Elem()
	}
	if t.PkgPath() != "" && !strings.Contains(name, "[") {
		return path.Base(t.PkgPath()) + "." + name
	}
	return name
}

// Empty ist das Ergebnis ohne Felder.
type Empty struct{}
