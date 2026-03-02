export type SDGValue = {
  prediction: number;
  sdg?: string | {
    "@type"?: string;
    code?: string;
    icon?: string;
    id?: string;
    label?: string;
    name?: string;
    type?: string;
  };
};

export type ResultsData = {
  projectUrl?: string;
  projectName?: string;
  predictions?: Record<string, SDGValue> | Record<string, number>;
  [key: string]: unknown;
};

export type ErrorProps = {
  error: string | null;
  setError: (error: string | null) => void;
  setResults: (
    results: {
      sdg_predictions?: Record<string, number>;
      [key: string]: unknown;
    } | null
  ) => void;
};

export type RawResultsProps = {
  results: unknown;
};
