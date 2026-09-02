"use client";

import { useState } from "react";
import { MapPin, FileCheck, DollarSign, Plane, ExternalLink, Sparkles } from "lucide-react";
import { generateLocationMatches, type LocationMatchResponse, type LocationMatch } from "@/lib/api";

interface LocationMatchPanelProps {
  reportId: string;
}

export function LocationMatchPanel({ reportId }: LocationMatchPanelProps) {
  const [data, setData] = useState<LocationMatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await generateLocationMatches(reportId);
      if (!res.success) throw new Error(res.error || "Location matching failed");
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to match locations");
    } finally {
      setLoading(false);
    }
  };

  const mapsUrl = (m: LocationMatch) =>
    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${m.matched_location} ${m.city} filming location`)}`;

  const totalCost = data?.matches.reduce((s, m) => s + (m.est_cost_usd || 0), 0) || 0;
  const permits = data?.matches.filter((m) => m.permit_required).length || 0;

  return (
    <div className="claim-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MapPin size={20} style={{ color: "var(--accent)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            Scene-to-Location Matcher
          </h3>
        </div>
        {!data && !loading && (
          <button
            onClick={run}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
            style={{ background: "linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%)", color: "white" }}
          >
            <Sparkles size={14} className="inline mr-1" /> Suggest Locations
          </button>
        )}
        {data && (
          <button
            onClick={run}
            className="px-3 py-1.5 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            🔄 Re-scout
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Scouting locations...</span>
        </div>
      )}

      {error && <p className="text-flagged py-4 text-center">{error}</p>}

      {data && !loading && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))" }}>
              <p className="text-lg font-bold" style={{ color: "var(--text)" }}>{data.match_count}</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Scenes scouted</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))" }}>
              <p className="text-lg font-bold" style={{ color: "var(--text)" }}>{permits}</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Need permits</p>
            </div>
            <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))" }}>
              <p className="text-lg font-bold" style={{ color: "var(--text)" }}>${(totalCost / 1000).toFixed(1)}k</p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Est. location cost</p>
            </div>
          </div>

          <div className="space-y-2">
            {data.matches.map((m, i) => (
              <div key={i} className="rounded-lg border p-3" style={{ borderColor: "var(--border)" }}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium text-sm" style={{ color: "var(--text)" }}>
                      <span className="mr-1">{i + 1}.</span>{m.matched_location}
                    </p>
                    <p className="text-xs" style={{ color: "var(--text-muted)" }}>{m.venue_type} · {m.city}</p>
                  </div>
                  <a
                    href={mapsUrl(m)}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-xs px-2 py-1 rounded"
                    style={{ border: "1px solid var(--border)", color: "var(--accent)" }}
                  >
                    <MapPin size={12} /> Map <ExternalLink size={10} />
                  </a>
                </div>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px]">
                  <span className={`px-1.5 py-0.5 rounded flex items-center gap-1 ${m.permit_required ? "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300" : "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"}`}>
                    <FileCheck size={10} /> {m.permit_required ? "Permit req." : "No permit"}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 flex items-center gap-1">
                    <DollarSign size={10} /> ${m.est_cost_usd.toLocaleString()}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 flex items-center gap-1">
                    <Plane size={10} /> {m.travel_note}
                  </span>
                </div>
                <p className="mt-1 text-[11px]" style={{ color: "var(--text-muted)" }}>{m.rationale}</p>
              </div>
            ))}
          </div>

          <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>
            Method: {data.generation_method === "gemini_ai" ? "AI location scout" : "Heuristic matcher"}.
            Map links use Google Maps search (no API key required).
          </p>
        </div>
      )}
    </div>
  );
}
