export interface CostListResult {
  entries: {
    id: string;
    at: string;
    person_id: string;
    provider: string;
    trigger: {
      kind: string;
      name: string;
      correlation_id: string;
      [k: string]: unknown;
    };
    quantity: {
      [k: string]: unknown;
    };
    amount_micro_eur: number;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
