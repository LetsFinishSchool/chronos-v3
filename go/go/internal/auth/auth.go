// Package auth: Bearer-Prüfung und OIDC-Code-Flow mit PKCE über Bibliotheken (go-oidc, oauth2). Keine eigene
// Token- oder Protokollimplementierung.
package auth

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"errors"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"golang.org/x/oauth2"

	"chronos/internal/config"
	"chronos/internal/db/sqlc"
	"chronos/internal/op"
)

const cookieName = "chronos_session"

type Auth struct {
	Cfg  *config.Config
	Pool *pgxpool.Pool
	Q    *sqlc.Queries

	mu       sync.Mutex
	provider *oidc.Provider
}

func New(cfg *config.Config, pool *pgxpool.Pool) *Auth {
	return &Auth{Cfg: cfg, Pool: pool, Q: sqlc.New(pool)}
}

// discover holt die Anbieter-Konfiguration (mit Wiederholung, Keycloak darf später starten als das Web).
func (a *Auth) discover(ctx context.Context) (*oidc.Provider, error) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.provider != nil {
		return a.provider, nil
	}
	p, err := oidc.NewProvider(ctx, a.Cfg.OIDCIssuer)
	if err != nil {
		return nil, err
	}
	a.provider = p
	return p, nil
}

type claims struct {
	Sub      string `json:"sub"`
	Username string `json:"preferred_username"`
	Email    string `json:"email"`
}

// verifyBearer prüft Signatur (JWKS), iss und exp; die Zielgruppe (aud) wird nicht geprüft (Access-Token von Keycloak).
func (a *Auth) verifyBearer(ctx context.Context, raw string) (op.Caller, error) {
	p, err := a.discover(ctx)
	if err != nil {
		return op.Caller{}, err
	}
	tok, err := p.Verifier(&oidc.Config{SkipClientIDCheck: true}).Verify(ctx, raw)
	if err != nil {
		return op.Caller{}, err
	}
	return a.person(ctx, tok)
}

func (a *Auth) person(ctx context.Context, tok *oidc.IDToken) (op.Caller, error) {
	var c claims
	if err := tok.Claims(&c); err != nil {
		return op.Caller{}, err
	}
	if c.Sub == "" {
		return op.Caller{}, errors.New("Token ohne sub")
	}
	if c.Username == "" {
		c.Username = c.Sub
	}
	if err := a.Q.UpsertPerson(ctx, sqlc.UpsertPersonParams{ID: c.Sub, Name: c.Username, Email: c.Email}); err != nil {
		return op.Caller{}, err
	}
	return op.Caller{ID: c.Sub, Name: c.Username, Email: c.Email}, nil
}

func bearer(r *http.Request) (string, bool) {
	h := r.Header.Get("Authorization")
	if len(h) > 7 && strings.EqualFold(h[:7], "bearer ") {
		return strings.TrimSpace(h[7:]), true
	}
	return "", false
}

// Middleware verlangt ein gültiges Bearer-Token (und mit allowCookie alternativ ein Sitzungscookie).
func (a *Auth) Middleware(allowCookie bool) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			c, err := a.authenticate(r, allowCookie)
			if err != nil {
				op.WriteError(w, op.Unauthenticated("gültige Anmeldung erforderlich"))
				return
			}
			next.ServeHTTP(w, r.WithContext(op.WithCaller(r.Context(), c)))
		})
	}
}

func (a *Auth) authenticate(r *http.Request, allowCookie bool) (op.Caller, error) {
	if raw, ok := bearer(r); ok {
		return a.verifyBearer(r.Context(), raw)
	}
	if allowCookie {
		if ck, err := r.Cookie(cookieName); err == nil && ck.Value != "" {
			p, err := a.Q.SessionPerson(r.Context(), ck.Value)
			if err != nil {
				return op.Caller{}, err
			}
			return op.Caller{ID: p.ID, Name: p.Name, Email: p.Email}, nil
		}
	}
	return op.Caller{}, errors.New("keine Anmeldung")
}

func (a *Auth) oauthConfig(p *oidc.Provider) *oauth2.Config {
	return &oauth2.Config{ClientID: a.Cfg.OIDCClientID, ClientSecret: a.Cfg.OIDCClientSecret, Endpoint: p.Endpoint(),
		RedirectURL: a.Cfg.OIDCRedirectURL, Scopes: []string{oidc.ScopeOpenID, "profile", "email"}}
}

func randomToken() string {
	b := make([]byte, 32)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}

// Mount hängt /auth/* ein.
func (a *Auth) Mount(mux interface {
	Get(string, http.HandlerFunc)
	Post(string, http.HandlerFunc)
}) {
	mux.Get("/auth/login", a.login)
	mux.Get("/auth/callback", a.callback)
	mux.Post("/auth/logout", a.logout)
	mux.Get("/auth/me", func(w http.ResponseWriter, r *http.Request) {
		a.Middleware(true)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			c, _ := op.CallerFrom(r.Context())
			op.WriteJSON(w, 200, map[string]string{"person_id": c.ID, "name": c.Name, "email": c.Email})
		})).ServeHTTP(w, r)
	})
}

func (a *Auth) login(w http.ResponseWriter, r *http.Request) {
	p, err := a.discover(r.Context())
	if err != nil {
		op.WriteError(w, op.Provider("Anmeldedienst nicht erreichbar"))
		return
	}
	state, verifier := randomToken(), oauth2.GenerateVerifier()
	if err := a.Q.InsertAuthFlow(r.Context(), sqlc.InsertAuthFlowParams{State: state, Verifier: verifier}); err != nil {
		op.WriteError(w, op.Internal("interner Fehler"))
		return
	}
	http.Redirect(w, r, a.oauthConfig(p).AuthCodeURL(state, oauth2.S256ChallengeOption(verifier)), http.StatusFound)
}

func (a *Auth) callback(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	verifier, err := a.Q.TakeAuthFlow(ctx, r.URL.Query().Get("state"))
	if errors.Is(err, pgx.ErrNoRows) || r.URL.Query().Get("code") == "" {
		http.Error(w, "ungültiger state", http.StatusBadRequest)
		return
	}
	if err != nil {
		op.WriteError(w, op.Internal("interner Fehler"))
		return
	}
	p, err := a.discover(ctx)
	if err != nil {
		op.WriteError(w, op.Provider("Anmeldedienst nicht erreichbar"))
		return
	}
	tok, err := a.oauthConfig(p).Exchange(ctx, r.URL.Query().Get("code"), oauth2.VerifierOption(verifier))
	if err != nil {
		op.WriteError(w, op.Provider("Code-Tausch fehlgeschlagen"))
		return
	}
	rawID, _ := tok.Extra("id_token").(string)
	idt, err := p.Verifier(&oidc.Config{ClientID: a.Cfg.OIDCClientID}).Verify(ctx, rawID)
	if err != nil {
		op.WriteError(w, op.Provider("ID-Token ungültig"))
		return
	}
	who, err := a.person(ctx, idt)
	if err != nil {
		op.WriteError(w, op.Internal("interner Fehler"))
		return
	}
	sid := randomToken()
	if err := a.Q.CreateSession(ctx, sqlc.CreateSessionParams{ID: sid, PersonID: who.ID}); err != nil {
		op.WriteError(w, op.Internal("interner Fehler"))
		return
	}
	http.SetCookie(w, &http.Cookie{Name: cookieName, Value: sid, Path: "/", HttpOnly: true, SameSite: http.SameSiteLaxMode})
	http.Redirect(w, r, "/", http.StatusFound)
}

func (a *Auth) logout(w http.ResponseWriter, r *http.Request) {
	if ck, err := r.Cookie(cookieName); err == nil {
		_ = a.Q.DeleteSession(r.Context(), ck.Value)
	}
	http.SetCookie(w, &http.Cookie{Name: cookieName, Value: "", Path: "/", HttpOnly: true, SameSite: http.SameSiteLaxMode,
		MaxAge: -1, Expires: time.Unix(0, 0)})
	w.WriteHeader(http.StatusNoContent)
}
