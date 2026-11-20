import { randomUUID } from "node:crypto";
import Fastify, { type FastifyRequest } from "fastify";
import fastifyCookie from "@fastify/cookie";
import fastifyStatic from "@fastify/static";
import { z } from "zod";
import { config } from "../core/config.js";
import { createDb, migrate } from "../core/db.js";
import { AppError } from "../core/errors.js";
import { rootLog, type Log } from "../core/logger.js";
import { aiTools, allOperations, describe, invoke, loadOperations, type Person } from "../core/operation.js";
import { createSession, finishLogin, personFromBearer, personFromSession, startLogin } from "./auth.js";
import { sql } from "kysely";

declare module "fastify" {
  interface FastifyRequest { correlationId: string; log2: Log }
}

const SESSION_COOKIE = "chronos_session";
const body = z.object({ params: z.record(z.string(), z.unknown()).optional(), preview: z.boolean().optional() }).strict();

export async function startWeb(): Promise<void> {
  const db = createDb(10);
  await migrate(db);
  await loadOperations();

  const app = Fastify({ logger: false, bodyLimit: 1_000_000 });
  await app.register(fastifyCookie);
  if (config.staticDir) await app.register(fastifyStatic, { root: config.staticDir, prefix: "/static/" });

  app.decorateRequest("correlationId", "");
  app.decorateRequest("log2", undefined as unknown as Log);
  app.addHook("onRequest", async (req, reply) => {
    const h = req.headers["x-correlation-id"];
    const given = Array.isArray(h) ? h[0] : h;
    req.correlationId = given && given.length <= 64 && /^[\x21-\x7e]+$/.test(given) ? given : randomUUID();
    req.log2 = rootLog.child({ correlation_id: req.correlationId });
    void reply.header("X-Correlation-Id", req.correlationId);
  });
  app.addHook("onResponse", async (req, reply) => {
    req.log2.info({ method: req.method, url: req.url.split("?")[0], status: reply.statusCode, ms: Math.round(reply.elapsedTime) }, "request");
  });

  const fail = (status: number, code: string, message: string) => ({ status, payload: { error: { code, message } } });
  app.setErrorHandler((err: Error & { statusCode?: number }, req, reply) => {
    if (err instanceof AppError) return reply.code(err.status).send({ error: { code: err.code, message: err.message } });
    if (err.statusCode && err.statusCode >= 400 && err.statusCode < 500) {
      const code = err.statusCode === 404 ? "not_found" : "validation_error";
      return reply.code(err.statusCode === 404 ? 404 : 422).send({ error: { code, message: err.message } });
    }
    req.log2.error({ err: err.stack ?? String(err) }, "unbehandelter Fehler");
    const f = fail(500, "internal", "Interner Fehler");
    return reply.code(f.status).send(f.payload);
  });
  app.setNotFoundHandler((_req, reply) => reply.code(404).send({ error: { code: "not_found", message: "Nicht gefunden" } }));

  async function authenticate(req: FastifyRequest): Promise<Person> {
    const auth = req.headers.authorization;
    if (auth) {
      const m = /^Bearer\s+(.+)$/i.exec(auth);
      if (!m || !m[1]) throw new AppError("unauthenticated", "Token fehlt oder ist ungültig");
      return personFromBearer(db, m[1]);
    }
    const sid = req.cookies[SESSION_COOKIE];
    const person = sid ? await personFromSession(db, sid) : undefined;
    if (!person) throw new AppError("unauthenticated", "Nicht angemeldet");
    return person;
  }

  app.get("/healthz", async (_req, reply) => {
    try {
      await sql`select 1`.execute(db);
      return { status: "ok" };
    } catch {
      return reply.code(503).send({ error: { code: "internal", message: "Datenbank nicht erreichbar" } });
    }
  });

  app.get("/api/v1/operations", async () => ({ operations: allOperations().map(describe) }));
  app.get("/api/v1/ai/tools", async () => ({ tools: aiTools() }));
  app.get("/api/v1/push/vapid-public-key", async () => ({ public_key: config.vapid.publicKey }));

  app.post<{ Params: { name: string } }>("/api/v1/operations/:name", async (req) => {
    const caller = await authenticate(req);
    const b = body.safeParse(req.body ?? {});
    if (!b.success) throw new AppError("validation_error", b.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; "));
    return invoke(req.params.name, b.data.params ?? {}, b.data.preview === true, {
      db, caller, correlationId: req.correlationId, log: req.log2,
      faultAfterHistory: config.faults && req.headers["x-spike-fault"] === "after_history",
    });
  });

  // --- Anmeldung (OIDC Code-Flow mit PKCE) ---
  app.get("/auth/login", async (_req, reply) => reply.redirect(await startLogin(db), 302));
  app.get("/auth/callback", async (req, reply) => {
    const query = req.url.includes("?") ? req.url.slice(req.url.indexOf("?") + 1) : "";
    let person: Person | undefined;
    try {
      person = await finishLogin(db, query);
    } catch (e) {
      req.log2.warn({ err: String(e) }, "Anmeldung fehlgeschlagen");
      throw new AppError("provider_error", "Anmeldung beim Identitätsanbieter fehlgeschlagen");
    }
    if (!person) return reply.code(400).send({ error: { code: "validation_error", message: "Ungültiger state" } });
    const sid = await createSession(db, person.id);
    void reply.setCookie(SESSION_COOKIE, sid, { httpOnly: true, sameSite: "lax", path: "/", secure: config.oidc.redirectUrl.startsWith("https:") });
    return reply.redirect("/", 302);
  });
  app.get("/auth/me", async (req) => {
    const p = await authenticate(req);
    return { person_id: p.id, name: p.name, email: p.email };
  });
  app.post("/auth/logout", async (req, reply) => {
    const sid = req.cookies[SESSION_COOKIE];
    if (sid) await db.deleteFrom("session").where("id", "=", sid).execute();
    void reply.clearCookie(SESSION_COOKIE, { path: "/" });
    return reply.code(204).send();
  });

  await app.listen({ port: config.port, host: "0.0.0.0" });
  rootLog.info({ port: config.port, operations: allOperations().length }, "web gestartet");
  const stop = async () => { await app.close(); await db.destroy(); process.exit(0); };
  process.on("SIGTERM", stop);
  process.on("SIGINT", stop);
}
