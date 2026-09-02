"use client";

import { useState } from "react";
import { GitCompare, Plus, Minus, Users } from "lucide-react";
import { DiffViewer } from "../DiffViewer";
import { compareScripts, type ScriptCompareResponse, type SceneDiff } from "@/lib/api";

interface ScriptComparePanelProps {
  reportId?: string;
}

const SCENE_BADGE: Record<string, string> = {
  added: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  removed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  modified: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
  unchanged: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
};

export function ScriptComparePanel({ reportId }: ScriptComparePanelProps) {
  const [otherScript, setOtherScript] = useState("");
  const [otherReportId, setOtherReportId] = useState("");
  const [data, setData] = useState<ScriptCompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"paste" | "report">("paste");

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: Record<string, string> = { label_a: "Current", label_b: "Other version" };
      if (reportId) payload.report_id_a = reportId;
      else if (!otherScript.trim()) throw new Error("Paste a script to compare.");

      if (mode === "paste") {
        if (!otherScript.trim()) throw new Error("Paste the other version's script.");
        payload.script_b = otherScript;
      } else {
        if (!otherReportId.trim()) throw new Error("Enter a report ID to compare against.");
        payload.report_id_b = otherReportId;
      }
      const res = await compareScripts(payload);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  const s = data?.summary;

  return (
    <div className="claim-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitCompare size={20} style={{ color: "var(--accent)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            Script Comparison / Version Diff
          </h3>
        </div>
      </div>

      {/* Inputs */}
      <div className="mb-4 space-y-3">
        <div className="flex gap-2">
          <button
            onClick={() => setMode("paste")}
            className={`px-3 py-1.5 rounded-lg text-sm ${mode === "paste" ? "font-semibold" : ""}`}
            style={mode === "paste" ? { background: "var(--accent)", color: "white" } : { border: "1px solid var(--border)", color: "var(--text)" }}
          >
            Paste script
          </button>
          <button
            onClick={() => setMode("report")}
            className={`px-3 py-1.5 rounded-lg text-sm ${mode === "report" ? "font-semibold" : ""}`}
            style={mode === "report" ? { background: "var(--accent)", color: "white" } : { border: "1px solid var(--border)", color: "var(--text)" }}
          >
            Compare report
          </button>
        </div>

        {mode === "paste" ? (
          <textarea
            value={otherScript}
            onChange={(e) => setOtherScript(e.target.value)}
            placeholder="Paste the other version of the script here..."
            rows={6}
            className="w-full rounded-lg p-3 text-sm font-mono"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          />
        ) : (
          <input
            value={otherReportId}
            onChange={(e) => setOtherReportId(e.target.value)}
            placeholder="Other report ID"
            className="w-full rounded-lg p-3 text-sm"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          />
        )}

        <button
          onClick={run}
          className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
          style={{ background: "linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%)", color: "white" }}
        >
          Compare Scripts
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Comparing scripts...</span>
        </div>
      )}

      {error && <p className="text-flagged py-4 text-center">{error}</p>}

      {data && !loading && (
        <div className="space-y-5">
          {/* Summary */}
          {s && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Stat label="Similarity" value={`${s.similarity_pct}%`} />
              <Stat label="Scenes Δ" value={`+${s.scenes_added}/-${s.scenes_removed}/~${s.scenes_modified}`} />
              <Stat label="Chars Δ" value={`+${s.characters_added}/-${s.characters_removed}`} />
              <Stat label="Lines Δ" value={`+${s.added_lines}/-${s.removed_lines}`} />
            </div>
          )}

          {/* Scene diff */}
          <div>
            <h4 className="text-sm font-semibold mb-2" style={{ color: "var(--text)" }}>
              Scene Changes
            </h4>
            <div className="space-y-2">
              {data.scenes.map((sc: SceneDiff, i) => (
                <div key={i} className="rounded-lg border p-3" style={{ borderColor: "var(--border)" }}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-sm" style={{ color: "var(--text)" }}>
                      Scene {sc.scene_number}: {sc.title}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${SCENE_BADGE[sc.status]}`}>
                      {sc.status}
                    </span>
                  </div>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>{sc.change}</p>
                  {(sc.characters_a.length > 0 || sc.characters_b.length > 0) && (
                    <div className="mt-1 flex flex-wrap gap-1 text-[11px]">
                      {sc.characters_a.map((c) => (
                        <span key={`a-${c}`} className="px-1.5 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 line-through">{c}</span>
                      ))}
                      {sc.characters_b.map((c) => (
                        <span key={`b-${c}`} className="px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">{c}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Character diff */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <CharBox title="Added" icon={<Plus size={14} />} items={data.characters.added} color="#22c55e" />
            <CharBox title="Removed" icon={<Minus size={14} />} items={data.characters.removed} color="#ef4444" />
            <CharBox title="Shared" icon={<Users size={14} />} items={data.characters.common} color="#60a5fa" />
          </div>

          {/* Line diff */}
          <div>
            <h4 className="text-sm font-semibold mb-2" style={{ color: "var(--text)" }}>
              Line-Level Diff
            </h4>
            <DiffViewer
              diff={data.line_diff.diff}
              addedLines={data.line_diff.added_lines}
              removedLines={data.line_diff.removed_lines}
              similarity={data.line_diff.similarity_percentage}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))" }}>
      <p className="text-lg font-bold" style={{ color: "var(--text)" }}>{value}</p>
      <p className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</p>
    </div>
  );
}

function CharBox({ title, icon, items, color }: { title: string; icon: React.ReactNode; items: string[]; color: string }) {
  return (
    <div className="p-3 rounded-lg" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))" }}>
      <div className="flex items-center gap-1.5 mb-2" style={{ color }}>
        {icon}
        <span className="text-xs font-semibold">{title} ({items.length})</span>
      </div>
      <div className="flex flex-wrap gap-1">
        {items.length === 0 ? (
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>—</span>
        ) : (
          items.map((c) => (
            <span key={c} className="px-1.5 py-0.5 rounded text-[11px]" style={{ backgroundColor: `${color}22`, color }}>{c}</span>
          ))
        )}
      </div>
    </div>
  );
}
