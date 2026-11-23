export interface SeriesOccurrencesResult {
  occurrences: {
    starts_at: string;
    ends_at: string;
    [k: string]: unknown;
  }[];
  [k: string]: unknown;
}
