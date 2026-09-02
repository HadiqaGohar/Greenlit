"use client";

import { useState, useEffect } from "react";

interface AnalysisProgressProps {
  isAnalyzing: boolean;
  progress: number;
  status: string;
  agentStatus?: Record<string, { status: string; progress?: number }>;
  estimatedTimeRemaining?: number;
  onCancel?: () => void;
}

export function AnalysisProgress({
  isAnalyzing,
  progress,
  status,
  agentStatus = {},
  estimatedTimeRemaining,
  onCancel,
}: AnalysisProgressProps) {
  const [displayProgress, setDisplayProgress] = useState(0);

  // Smooth progress animation
  useEffect(() => {
    if (!isAnalyzing) {
      setDisplayProgress(progress);
      return;
    }
    const diff = progress - displayProgress;
    if (diff <= 0) return;
    const step = Math.max(1, Math.ceil(diff / 10));
    const timer = setInterval(() => {
      setDisplayProgress((prev) => {
        const next = prev + step;
        if (next >= progress) {
          clearInterval(timer);
          return progress;
        }
        return next;
      });
    }, 50);
    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progress, isAnalyzing]);

  if (!isAnalyzing && progress === 0) return null;

  const agents = Object.entries(agentStatus);
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `~${Math.ceil(seconds)}s remaining`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.ceil(seconds % 60);
    return `~${mins}m ${secs}s remaining`;
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isAnalyzing && (
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          )}
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {isAnalyzing ? "Analyzing Script..." : progress >= 100 ? "Analysis Complete" : "Analysis Paused"}
          </h3>
        </div>
        {isAnalyzing && onCancel && (
          <button
            onClick={onCancel}
            className="rounded-md px-3 py-1 text-xs font-medium text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            Cancel
          </button>
        )}
      </div>

      {/* Main progress bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1.5">
          <span>{status}</span>
          <span>{Math.round(displayProgress)}%</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              progress >= 100
                ? "bg-green-500"
                : progress > 70
                  ? "bg-blue-500"
                  : "bg-amber-500"
            }`}
            style={{ width: `${displayProgress}%` }}
          />
        </div>
      </div>

      {/* Time remaining */}
      {isAnalyzing && estimatedTimeRemaining !== undefined && estimatedTimeRemaining > 0 && (
        <p className="mb-3 text-xs text-gray-500 dark:text-gray-400">
          {formatTime(estimatedTimeRemaining)}
        </p>
      )}

      {/* Agent statuses */}
      {agents.length > 0 && (
        <div className="space-y-2 mt-4">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Agent Progress</p>
          {agents.map(([name, agent]) => (
            <div key={name} className="flex items-center gap-3">
              <span className="w-24 text-xs font-medium text-gray-700 dark:text-gray-300 capitalize">
                {name}
              </span>
              <div className="flex-1 h-1.5 overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    agent.status === "complete"
                      ? "bg-green-500"
                      : agent.status === "error"
                        ? "bg-red-500"
                        : "bg-blue-500"
                  }`}
                  style={{ width: `${agent.progress ?? (agent.status === "complete" ? 100 : agent.status === "error" ? 100 : 50)}%` }}
                />
              </div>
              <span className="w-16 text-right text-[10px] text-gray-500 dark:text-gray-400">
                {agent.status === "complete"
                  ? "Done"
                  : agent.status === "error"
                    ? "Failed"
                    : agent.status === "running"
                      ? "Running..."
                      : "Queued"}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Completion message */}
      {!isAnalyzing && progress >= 100 && (
        <div className="mt-3 flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700 dark:bg-green-900/20 dark:text-green-300">
          <span>Analysis complete! Redirecting to report...</span>
        </div>
      )}
    </div>
  );
}
