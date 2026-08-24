"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect, useCallback } from "react";

import { ScriptEditor } from "@/components/ScriptEditor";
import { AnalysisProgress } from "@/components/AnalysisProgress";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { ShortcutHelp } from "@/components/ShortcutHelp";

export default function AnalyzePage() {
  const router = useRouter();
  const [scriptText, setScriptText] = useState("");
  const {
    isLoading,
    error,
    report,
    progress,
    status,
    agentStatus,
    estimatedTimeRemaining,
    analyze,
    reset,
  } = useAnalysis();

  const handleShortcutAction = useCallback(
    (key: string) => {
      switch (key) {
        case "a":
          if (scriptText.trim() && !isLoading) {
            analyze(scriptText);
          }
          break;
        case "n":
          setScriptText("");
          reset();
          break;
        case "d":
          router.push("/dashboard");
          break;
        case "s":
          router.push("/settings");
          break;
        case "Escape":
          if (isLoading) {
            reset();
          } else {
            router.push("/");
          }
          break;
      }
    },
    [scriptText, isLoading, analyze, reset, router],
  );

  const shortcuts = [
    { key: "a", description: "Analyze script", category: "Actions" },
    { key: "n", description: "New script", category: "Actions" },
    { key: "d", description: "Go to Dashboard", category: "Navigation" },
    { key: "s", description: "Go to Settings", category: "Navigation" },
    { key: "Escape", description: "Cancel / Go back", category: "General" },
    { key: "?", description: "Show shortcuts", category: "General" },
  ];

  const { showHelp, setShowHelp } = useKeyboardShortcuts({
    shortcuts,
    onAction: handleShortcutAction,
  });

  // Redirect to report when done
  useEffect(() => {
    if (report && progress >= 100 && !isLoading) {
      const timer = setTimeout(() => {
        router.push(`/report/${report.report_id}`);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [report, progress, isLoading, router]);

  const handleSubmit = async () => {
    const trimmed = scriptText.trim();
    if (!trimmed || isLoading) return;
    await analyze(trimmed);
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <ShortcutHelp isOpen={showHelp} onClose={() => setShowHelp(false)} />

      <section className="mb-10 text-center">
        <h1
          className="font-display text-4xl font-semibold tracking-tight"
          style={{ color: "var(--text)" }}
        >
          Script Research
        </h1>
        <p className="mx-auto mt-3 max-w-lg" style={{ color: "var(--text-muted)" }}>
          Paste a script or scene — GreenLit AI extracts factual claims, researches
          them live, and returns production notes with sources.
        </p>
        <p className="mt-2 text-xs" style={{ color: "var(--text-muted)" }}>
          Press <kbd className="rounded border border-gray-300 px-1 dark:border-gray-600">?</kbd> for keyboard shortcuts
        </p>
      </section>

      {/* Progress indicator */}
      {(isLoading || progress > 0) && (
        <div className="mb-6">
          <AnalysisProgress
            isAnalyzing={isLoading}
            progress={progress}
            status={status}
            agentStatus={agentStatus}
            estimatedTimeRemaining={estimatedTimeRemaining ?? undefined}
            onCancel={isLoading ? reset : undefined}
          />
        </div>
      )}

      {!isLoading && (
        <div className="space-y-6">
          <ScriptEditor
            value={scriptText}
            onChange={setScriptText}
            disabled={isLoading}
          />

          {error && (
            <p
              className="rounded-lg px-4 py-3 text-sm"
              style={{
                border: "1px solid var(--flagged)",
                backgroundColor: "rgba(192, 57, 43, 0.1)",
                color: "var(--flagged)",
              }}
            >
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!scriptText.trim() || isLoading}
            className="w-full rounded-lg px-6 py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40"
            style={{
              backgroundColor: "var(--accent)",
              color: "var(--accent-contrast)",
            }}
          >
            {isLoading ? "Analyzing..." : "Analyze Script"}
          </button>
        </div>
      )}
    </div>
  );
}
