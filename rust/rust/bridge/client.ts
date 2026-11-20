import type { OperationMap, OperationName } from "./generated/operations";

export type { OperationMap, OperationName };

export class ChronosError extends Error {
  constructor(readonly status: number, readonly code: string, message: string) {
    super(message);
  }
}

/** Typisierter Client: Parameter und Ergebnis ergeben sich aus dem Operationsnamen (generierte Typen). */
export function createClient(baseUrl: string, getToken: () => string) {
  async function post<N extends OperationName>(name: N, params: OperationMap[N]["params"], preview: boolean): Promise<any> {
    const res = await fetch(`${baseUrl}/api/v1/operations/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ params, preview }),
    });
    const body = await res.json();
    if (!res.ok) throw new ChronosError(res.status, body?.error?.code ?? "internal", body?.error?.message ?? res.statusText);
    return body;
  }
  return {
    async call<N extends OperationName>(name: N, params: OperationMap[N]["params"]): Promise<OperationMap[N]["result"]> {
      return (await post(name, params, false)).result;
    },
    async preview<N extends OperationName>(name: N, params: OperationMap[N]["params"]): Promise<{ count: number; affected: { type: string; id: string; change: string }[] }> {
      return (await post(name, params, true)).preview;
    },
  };
}
