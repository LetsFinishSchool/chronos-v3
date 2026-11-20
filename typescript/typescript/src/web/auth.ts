import { createRemoteJWKSet, jwtVerify } from "jose";
import * as oidc from "openid-client";
import { randomBytes } from "node:crypto";
import type { Kysely } from "kysely";
import { config } from "../core/config.js";
import type { Database } from "../core/db.js";
import { AppError } from "../core/errors.js";
import type { Person } from "../core/operation.js";

// Token-Prüfung (Signatur über JWKS, iss, exp) übernimmt `jose`; den Code-Flow mit PKCE `openid-client`.
const jwks = createRemoteJWKSet(new URL(`${config.oidc.issuer}/protocol/openid-connect/certs`));

const known = new Map<string, { key: string; at: number }>();

/** Legt die Person beim ersten authentifizierten Zugriff an oder aktualisiert sie (kurz zwischengespeichert). */
export async function upsertPerson(db: Kysely<Database>, p: Person): Promise<Person> {
  const key = `${p.name}\u0000${p.email ?? ""}`;
  const c = known.get(p.id);
  if (c && c.key === key && Date.now() - c.at < 60_000) return p;
  await db.insertInto("person").values({ id: p.id, name: p.name, email: p.email })
    .onConflict((oc) => oc.column("id").doUpdateSet({ name: p.name, email: p.email })).execute();
  known.set(p.id, { key, at: Date.now() });
  return p;
}

export async function personFromBearer(db: Kysely<Database>, token: string): Promise<Person> {
  try {
    const { payload } = await jwtVerify(token, jwks, { issuer: config.oidc.issuer });
    if (!payload.sub) throw new Error("sub fehlt");
    const name = typeof payload["preferred_username"] === "string" ? payload["preferred_username"] : payload.sub;
    const email = typeof payload["email"] === "string" ? payload["email"] : null;
    return await upsertPerson(db, { id: payload.sub, name, email });
  } catch (e) {
    if (e instanceof AppError) throw e;
    throw new AppError("unauthenticated", "Token fehlt oder ist ungültig");
  }
}

export async function personFromSession(db: Kysely<Database>, sessionId: string): Promise<Person | undefined> {
  const r = await db.selectFrom("session").innerJoin("person", "person.id", "session.person_id")
    .select(["person.id", "person.name", "person.email"]).where("session.id", "=", sessionId).executeTakeFirst();
  return r;
}

export async function createSession(db: Kysely<Database>, personId: string): Promise<string> {
  const id = randomBytes(32).toString("base64url");
  await db.insertInto("session").values({ id, person_id: personId }).execute();
  return id;
}

let discovered: Promise<oidc.Configuration> | undefined;
function oidcConfig(): Promise<oidc.Configuration> {
  discovered ??= oidc.discovery(new URL(config.oidc.issuer), config.oidc.clientId, config.oidc.clientSecret, undefined, {
    execute: config.oidc.issuer.startsWith("http:") ? [oidc.allowInsecureRequests] : [],
  }).catch((e) => { discovered = undefined; throw e; });
  return discovered;
}

export async function startLogin(db: Kysely<Database>): Promise<string> {
  const cfg = await oidcConfig();
  const verifier = oidc.randomPKCECodeVerifier();
  const state = oidc.randomState();
  await db.deleteFrom("oidc_state").where("created_at", "<", new Date(Date.now() - 10 * 60_000)).execute();
  await db.insertInto("oidc_state").values({ state, verifier }).execute();
  return oidc.buildAuthorizationUrl(cfg, {
    redirect_uri: config.oidc.redirectUrl, scope: "openid email profile",
    code_challenge: await oidc.calculatePKCECodeChallenge(verifier), code_challenge_method: "S256", state,
  }).href;
}

/** Schließt den Code-Flow ab. Gibt undefined bei unbekanntem `state` zurück (→ 400). */
export async function finishLogin(db: Kysely<Database>, query: string): Promise<Person | undefined> {
  const state = new URLSearchParams(query).get("state");
  if (!state) return undefined;
  const row = await db.deleteFrom("oidc_state").where("state", "=", state).returning("verifier").executeTakeFirst();
  if (!row) return undefined;
  const cfg = await oidcConfig();
  const current = new URL(config.oidc.redirectUrl);
  current.search = query;
  const tokens = await oidc.authorizationCodeGrant(cfg, current, { pkceCodeVerifier: row.verifier, expectedState: state });
  const c = tokens.claims();
  if (!c?.sub) throw new Error("id_token ohne sub");
  return upsertPerson(db, {
    id: c.sub, name: typeof c["preferred_username"] === "string" ? c["preferred_username"] : c.sub, email: typeof c["email"] === "string" ? c["email"] : null,
  });
}
