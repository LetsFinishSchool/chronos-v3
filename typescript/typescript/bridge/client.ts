import type { Operations } from "./generated/operations";

export type { Operations };

export class ApiError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
  }
}

/** Typisierter Client: `call(name, params)` – Parameter und Ergebnis folgen dem Operationsnamen. */
export function createClient(baseUrl: string, getToken: () => string) {
  async function call<N extends keyof Operations>(name: N, params: Operations[N]["params"]): Promise<Operations[N]["result"]> {
    const res = await fetch(`${baseUrl}/api/v1/operations/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ params }),
    });
    const body = (await res.json()) as { result?: Operations[N]["result"]; error?: { code: string; message: string } };
    if (!res.ok || body.result === undefined) throw new ApiError(res.status, body.error?.code ?? "internal", body.error?.message ?? res.statusText);
    return body.result;
  }
  return { call };
}
