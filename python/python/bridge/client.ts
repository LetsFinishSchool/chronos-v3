import type { Operations } from "./generated/operations";

export type OperationName = keyof Operations;

export class ChronosApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

/** Typisierter Client: `params` und Ergebnis hängen vom Operationsnamen ab (Typen kommen aus /api/v1/operations). */
export function createClient(baseUrl: string, getToken: () => string) {
  return {
    async call<N extends OperationName>(name: N, params: Operations[N]["params"]): Promise<Operations[N]["result"]> {
      const res = await fetch(`${baseUrl}/api/v1/operations/${name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ params }),
      });
      const body = await res.json();
      if (!res.ok) throw new ChronosApiError(res.status, body.error?.code ?? "internal", body.error?.message ?? "");
      return body.result;
    },
  };
}
