"use client";

import {
  createContext,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  useContext,
  useState,
} from "react";
import { ResultsData } from "@/types/main";

type AppStateContextValue = {
  results: ResultsData | null;
  setResults: Dispatch<SetStateAction<ResultsData | null>>;
  error: string | null;
  setError: Dispatch<SetStateAction<string | null>>;
};

const AppStateContext = createContext<AppStateContextValue | undefined>(
  undefined,
);

export const AppStateProvider = ({ children }: { children: ReactNode }) => {
  const [results, setResults] = useState<ResultsData | null>(null);
  const [error, setError] = useState<string | null>(null);

  return (
    <AppStateContext.Provider value={{ results, setResults, error, setError }}>
      {children}
    </AppStateContext.Provider>
  );
};

export const useAppState = () => {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error("useAppState must be used within AppStateProvider");
  }
  return context;
};
