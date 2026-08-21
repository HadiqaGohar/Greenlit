"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { LoadingReel } from "@/components/LoadingReel";
import { ScriptEditor } from "@/components/ScriptEditor";
import { useAnalysis } from "@/hooks/useAnalysis";

export default function AnalyzePage() {
  const router = useRouter();
  const [scriptText, setScriptText] = useState("");
  const { isLoading, error, analyze } = useAnalysis();

  const handleSubmit = async () => {
    const trimmed = scriptText.trim();
    if (!trimmed) return;

    const report = await analyze(trimmed);
    if (report) {
      router.push(`/report/${report.report_id}`);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <section className="mb-10 text-center">
        <h1 className="font-display text-4xl font-semibold tracking-tight" style={{ color: 'var(--text)' }}>
          Script Research
        </h1>
        <p className="mx-auto mt-3 max-w-lg" style={{ color: 'var(--text-muted)' }}>
          Paste a script or scene — GreenLit AI extracts factual claims,
          researches them live, and returns production notes with sources.
        </p>
      </section>

      {isLoading ? (
        <LoadingReel />
      ) : (
        <div className="space-y-6">
          <ScriptEditor
            value={scriptText}
            onChange={setScriptText}
            disabled={isLoading}
          />

          {error && (
            <p className="rounded-lg px-4 py-3 text-sm" 
               style={{ 
                 border: '1px solid var(--flagged)',
                 backgroundColor: 'rgba(192, 57, 43, 0.1)',
                 color: 'var(--flagged)'
               }}>
              {error}
            </p>
          )}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!scriptText.trim() || isLoading}
            className="w-full rounded-lg px-6 py-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-40"
            style={{
              backgroundColor: 'var(--accent)',
              color: 'var(--accent-contrast)'
            }}
          >
            Analyze Script
          </button>
        </div>
      )}
    </div>
  );
}
