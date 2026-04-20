import React from "react";
import { RiErrorWarningFill } from "react-icons/ri";
import { useAppState } from "@/lib/appStateContext";

/*
Error Component
- Displays an error message when analysis fails
- Shows a warning icon, error details, and a "Try Again" button

*/

const Error = () => {
  const { error, setError, setResults } = useAppState();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br">
      <div className="text-center space-y-6 max-w-md">
        <div className="text-red-500">
          <RiErrorWarningFill className="w-20 h-20 mx-auto mb-4" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-red-600">Analysis Failed</h2>
          <p className="text-gray-600 text-lg">{error}</p>
        </div>
        <button
          onClick={() => {
            setError(null);
            setResults(null);
          }}
          className="px-6 py-3 bg-purple-700 hover:bg-purple-800 text-white font-semibold rounded-xl transition-colors duration-200"
        >
          Try Again
        </button>
      </div>
    </div>
  );
};

export default Error;
