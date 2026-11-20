import type { OperationMap } from "./generated/operations";

export type OperationName = keyof OperationMap;

export interface Client {
  call<N extends OperationName>(name: N, params: OperationMap[N]["params"]): Promise<OperationMap[N]["result"]>;
}

export function createClient(baseUrl: string, getToken: () => string): Client {
  return {
    async call(name, params) {
      const res = await fetch(`${baseUrl}/api/v1/operations/${name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ params }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(`${body?.error?.code ?? res.status}: ${body?.error?.message ?? ""}`);
      return body.result;
    },
  };
}
