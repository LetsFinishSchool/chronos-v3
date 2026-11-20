import { beforeAll, expect, test } from "vitest";
import { aiTools, allOperations, describe, loadOperations } from "./operation.js";

beforeAll(loadOperations);

test("Werkzeuge und Beschreibung stammen aus derselben Operationsliste", () => {
  const ops = allOperations();
  expect(ops.length).toBeGreaterThanOrEqual(18);
  const tools = aiTools();
  expect(tools.map((t) => t.name)).toEqual(ops.map((o) => o.name.replaceAll(".", "_")));
  for (const [i, op] of ops.entries()) {
    expect(tools[i]!.input_schema).toEqual(describe(op).params_schema);
    expect(describe(op).params_schema).toMatchObject({ type: "object", additionalProperties: false });
  }
});
