import type { OperationMap } from "./generated/operations";

export type OperationName = keyof OperationMap;
export type Params<N extends OperationName> = OperationMap[N]["params"];
export type Result<N extends OperationName> = OperationMap[N]["result"];

export function createClient(baseUrl: string, getToken: () => string) {
  return {
    async call<N extends OperationName>(name: N, params: Params<N>): Promise<Result<N>> {
      const r = await fetch(`${baseUrl}/api/v1/operations/${name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ params }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error?.message ?? String(r.status));
      return j.result as Result<N>;
    },
  };
}
