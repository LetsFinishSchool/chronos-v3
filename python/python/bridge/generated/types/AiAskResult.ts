export interface AiAskResult {
  text: string;
  proposed_calls: {
    name: string;
    input: {
      [k: string]: unknown;
    };
    [k: string]: unknown;
  }[];
  usage: {
    input_tokens: number;
    output_tokens: number;
    [k: string]: unknown;
  };
  [k: string]: unknown;
}
