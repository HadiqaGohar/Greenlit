"use client";

import { useCallback, useState } from "react";

import { analyzeScript, ApiError } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

interface UseAnalysisState {
  isLoading: boolean;
  error: string | null;
  report: AnalyzeResponse | null;
}

export function useAnalysis() {
  const [state, setState] = useState<UseAnalysisState>({
    isLoading: false,
    error: null,
    report: null,
  });

  const analyze = useCallback(async (scriptText: string) => {
    setState({ isLoading: true, error: null, report: null });

    try {
      const report = await analyzeScript({ script_text: scriptText });
      setState({ isLoading: false, error: null, report });
      return report;
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.";
      setState({ isLoading: false, error: message, report: null });
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState({ isLoading: false, error: null, report: null });
  }, []);

  return { ...state, analyze, reset };
}
