"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Presentation, ChevronLeft, ChevronRight, Download, Sparkles } from "lucide-react";
import { generatePitchDeck, type PitchDeckResponse } from "@/lib/api";

interface PitchDeckPanelProps {
  reportId: string;
}

const SLIDE_ICONS: Record<string, string> = {
  Logline: "🎯",
  Synopsis: "📝",
  "Genre & Tone": "🎬",
  "Key Characters": "👥",
  Themes: "💡",
  "Visual Style": "🎨",
  "Target Audience": "🎯",
  "Comparable Films": "🎞️",
  "Production Scale": "🏗️",
  "Risks & Opportunities": "⚠️",
};

export function PitchDeckPanel({ reportId }: PitchDeckPanelProps) {
  const [data, setData] = useState<PitchDeckResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await generatePitchDeck(reportId);
      if (!res.success) throw new Error(res.error || "Pitch deck generation failed");
      setData(res);
      setIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate pitch deck");
    } finally {
      setLoading(false);
    }
  };

  const exportMarkdown = () => {
    if (!data) return;
    const md = `# ${data.title}\n\n` + data.slides.map((s) => `## ${s.title}\n` + s.bullets.map((b) => `- ${b}`).join("\n")).join("\n\n");
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.title.replace(/\s+/g, "_")}_pitch_deck.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const total = data?.slides.length || 0;
  const current = data?.slides[index];

  return (
    <div className="claim-card rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Presentation size={20} style={{ color: "var(--accent)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            AI Pitch Deck Generator
          </h3>
        </div>
        {!data && !loading && (
          <button
            onClick={run}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
            style={{ background: "linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%)", color: "white" }}
          >
            <Sparkles size={14} className="inline mr-1" /> Generate Deck
          </button>
        )}
        {data && (
          <div className="flex gap-2">
            <button
              onClick={exportMarkdown}
              className="px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1"
              style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
            >
              <Download size={14} /> Export
            </button>
            <button
              onClick={run}
              className="px-3 py-1.5 rounded-lg text-sm font-medium"
              style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
            >
              🔄 Regenerate
            </button>
          </div>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Building your pitch deck...</span>
        </div>
      )}

      {error && <p className="text-flagged py-4 text-center">{error}</p>}

      {data && !loading && current && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold" style={{ color: "var(--text)" }}>{data.title}</span>
            <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))", color: "var(--text-muted)" }}>
              {data.generation_method === "gemini_ai" ? "AI-generated" : "Auto draft"}
            </span>
          </div>

          {/* Slide card (16:9) */}
          <div
            className="relative w-full overflow-hidden rounded-xl p-8 flex flex-col justify-center"
            style={{
              aspectRatio: "16 / 9",
              background: "linear-gradient(135deg, rgba(124,58,237,0.15), rgba(59,130,246,0.10))",
              border: "1px solid var(--border)",
            }}
          >
            <AnimatePresence mode="wait">
              <motion.div
                key={index}
                initial={{ opacity: 0, x: 40 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -40 }}
                transition={{ duration: 0.3 }}
                className="w-full"
              >
                <div className="flex items-center gap-2 mb-4">
                  <span className="text-3xl">{SLIDE_ICONS[current.title] || "📌"}</span>
                  <h4 className="text-2xl font-bold" style={{ color: "var(--text)" }}>{current.title}</h4>
                </div>
                <ul className="space-y-2">
                  {current.bullets.map((b, i) => (
                    <li key={i} className="flex items-start gap-2 text-base" style={{ color: "var(--text)" }}>
                      <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full" style={{ backgroundColor: "var(--accent)" }} />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            </AnimatePresence>

            <span className="absolute bottom-3 right-4 text-xs" style={{ color: "var(--text-muted)" }}>
              {index + 1} / {total}
            </span>
          </div>

          {/* Progress + nav */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIndex((i) => Math.max(0, i - 1))}
              disabled={index === 0}
              className="p-2 rounded-lg disabled:opacity-40"
              style={{ border: "1px solid var(--border)", color: "var(--text)" }}
            >
              <ChevronLeft size={18} />
            </button>
            <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${((index + 1) / total) * 100}%`, backgroundColor: "var(--accent)" }}
              />
            </div>
            <button
              onClick={() => setIndex((i) => Math.min(total - 1, i + 1))}
              disabled={index === total - 1}
              className="p-2 rounded-lg disabled:opacity-40"
              style={{ border: "1px solid var(--border)", color: "var(--text)" }}
            >
              <ChevronRight size={18} />
            </button>
          </div>

          {/* Slide thumbnails */}
          <div className="flex flex-wrap gap-1.5">
            {data.slides.map((sl, i) => (
              <button
                key={i}
                onClick={() => setIndex(i)}
                className={`px-2 py-1 rounded text-xs ${i === index ? "font-semibold" : ""}`}
                style={i === index ? { backgroundColor: "var(--accent)", color: "white" } : { border: "1px solid var(--border)", color: "var(--text-muted)" }}
              >
                {sl.title}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
