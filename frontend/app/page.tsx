"use client";

import Results from "@/components/results";
import Error from "@/components/error";
import MainScreen from "@/components/mainScreen";
import { AppStateProvider, useAppState } from "@/lib/appStateContext";

/**
 * Main Application Component - UN SDG Advocate
 *
 * Flow:
 * 1. User enters Project Name, GitHub repository URL and project SDG relevance description
 * 2. The data is then sent to Flask backend for analysis
 * 4. Results show SDG predictions with confidence levels
 * 5. User can edit predictions via modal interface
 * 6. Edited results are saved and stored in state
 */
export default function Home() {
  return (
    <AppStateProvider>
      <HomeContent />
    </AppStateProvider>
  );
}

const HomeContent = () => {
  const { results, error } = useAppState();

  console.log("Current Results State:", results);

  return (
    <div className="min-h-screen bg-gradient-to-br">
      {results ? <Results /> : error ? <Error /> : <MainScreen />}
    </div>
  );
};
