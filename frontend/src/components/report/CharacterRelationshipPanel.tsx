"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Users, Link2, Star } from "lucide-react";
import {
  generateRelationshipGraph,
  type RelationshipResponse,
  type RelationshipEdge,
  type RelationshipNode,
} from "@/lib/api";

interface CharacterRelationshipPanelProps {
  reportId: string;
}

const RELATIONSHIP_COLORS: Record<string, string> = {
  family: "#ec4899",
  romantic: "#f43f5e",
  rivalry: "#ef4444",
  authority: "#f59e0b",
  ally: "#22c55e",
  associate: "#60a5fa",
};

const RELATIONSHIP_LABELS: Record<string, string> = {
  family: "Family",
  romantic: "Romantic",
  rivalry: "Rivalry",
  authority: "Authority",
  ally: "Ally",
  associate: "Associate",
};

const VB_W = 620;
const VB_H = 520;
const CX = VB_W / 2;
const CY = VB_H / 2;

export function CharacterRelationshipPanel({ reportId }: CharacterRelationshipPanelProps) {
  const [data, setData] = useState<RelationshipResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await generateRelationshipGraph(reportId);
      if (!res.success) throw new Error(res.error || "Relationship analysis failed");
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to analyze relationships");
    } finally {
      setLoading(false);
    }
  };

  const layout = useMemo(() => {
    if (!data) return { positions: {} as Record<string, { x: number; y: number }> };
    const nodes = data.nodes;
    const n = nodes.length;
    const radius = Math.min(VB_W, VB_H) / 2 - 90;
    const positions: Record<string, { x: number; y: number }> = {};
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / Math.max(1, n) - Math.PI / 2;
      positions[node.id] = {
        x: CX + radius * Math.cos(angle),
        y: CY + radius * Math.sin(angle),
      };
    });
    return { positions };
  }, [data]);

  const maxWeight = useMemo(
    () => (data ? Math.max(1, ...data.edges.map((e) => e.weight)) : 1),
    [data],
  );

  const isEdgeActive = (e: RelationshipEdge) =>
    !hovered || e.source === hovered || e.target === hovered;

  return (
    <div className="claim-card rounded-xl p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users size={20} style={{ color: "var(--accent)" }} />
          <h3 className="font-display text-lg font-semibold" style={{ color: "var(--text)" }}>
            Character Relationship Graph
          </h3>
        </div>
        {!data && !loading && (
          <button
            onClick={run}
            className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
            style={{ background: "linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%)", color: "white" }}
          >
            Generate Graph
          </button>
        )}
        {data && (
          <button
            onClick={run}
            className="px-3 py-1.5 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            🔄 Re-generate
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: "var(--accent)" }} />
          <span className="ml-3" style={{ color: "var(--text-muted)" }}>Mapping character relationships...</span>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <p className="text-flagged mb-4">{error}</p>
          <button
            onClick={run}
            className="px-4 py-2 rounded-lg text-sm font-medium"
            style={{ backgroundColor: "var(--bg)", color: "var(--text)", border: "1px solid var(--border)" }}
          >
            Try Again
          </button>
        </div>
      )}

      {data && !loading && (
        <div className="space-y-5">
          {/* Stats */}
          <div className="grid grid-cols-3 gap-3">
            <Stat icon={<Users size={16} />} label="Characters" value={data.stats.character_count} />
            <Stat icon={<Link2 size={16} />} label="Relationships" value={data.stats.relationship_count} />
            <Stat icon={<Star size={16} />} label="Most Connected" value={data.stats.most_connected || "—"} small />
          </div>

          {/* Graph */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="flex justify-center"
          >
            <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="w-full max-w-2xl" style={{ maxHeight: 520 }}>
              {/* Edges */}
              {data.edges.map((e, i) => {
                const a = layout.positions[e.source];
                const b = layout.positions[e.target];
                if (!a || !b) return null;
                const active = isEdgeActive(e);
                const mx = (a.x + b.x) / 2;
                const my = (a.y + b.y) / 2;
                const color = RELATIONSHIP_COLORS[e.type] || RELATIONSHIP_COLORS.associate;
                const w = 1 + (e.weight / maxWeight) * 7;
                return (
                  <g key={i} opacity={active ? 1 : 0.12} style={{ transition: "opacity 0.2s" }}>
                    <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={color} strokeWidth={w} strokeLinecap="round" />
                    <circle cx={mx} cy={my} r={3} fill={color} />
                  </g>
                );
              })}

              {/* Nodes */}
              {data.nodes.map((node: RelationshipNode) => {
                const pos = layout.positions[node.id];
                if (!pos) return null;
                const r = 14 + node.centrality * 14;
                const active = !hovered || isEdgeActive({ source: node.id, target: node.id } as RelationshipEdge) ||
                  data.edges.some((e) => (e.source === node.id || e.target === node.id) && (e.source === hovered || e.target === hovered));
                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    opacity={hovered && !active ? 0.3 : 1}
                    style={{ transition: "opacity 0.2s", cursor: "pointer" }}
                    onMouseEnter={() => setHovered(node.id)}
                    onMouseLeave={() => setHovered(null)}
                  >
                    <circle
                      r={r}
                      fill={node.is_primary ? "var(--accent)" : "var(--surface, #334155)"}
                      stroke={node.is_primary ? "#fff" : "var(--border)"}
                      strokeWidth={node.is_primary ? 2.5 : 1.5}
                    />
                    <text
                      y={r + 14}
                      textAnchor="middle"
                      fontSize={node.is_primary ? 13 : 11}
                      fontWeight={node.is_primary ? 700 : 500}
                      fill="var(--text)"
                    >
                      {node.name.length > 16 ? node.name.slice(0, 15) + "…" : node.name}
                    </text>
                  </g>
                );
              })}
            </svg>
          </motion.div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 justify-center">
            {Object.entries(RELATIONSHIP_LABELS).map(([type, label]) => (
              <div key={type} className="flex items-center gap-1.5">
                <span className="h-3 w-3 rounded-full" style={{ backgroundColor: RELATIONSHIP_COLORS[type] }} />
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>{label}</span>
              </div>
            ))}
          </div>

          {/* Relationship list */}
          <div>
            <h4 className="text-sm font-semibold mb-2" style={{ color: "var(--text)" }}>
              Relationship Details
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ color: "var(--text-muted)" }} className="text-left border-b">
                    <th className="py-2 pr-2 font-medium">Character A</th>
                    <th className="py-2 pr-2 font-medium">Type</th>
                    <th className="py-2 pr-2 font-medium">Character B</th>
                    <th className="py-2 pr-2 font-medium">Shared</th>
                    <th className="py-2 font-medium">Scenes</th>
                  </tr>
                </thead>
                <tbody>
                  {data.edges.map((e, i) => (
                    <tr key={i} className="border-b" style={{ borderColor: "var(--border)" }}>
                      <td className="py-2 pr-2 font-medium" style={{ color: "var(--text)" }}>{e.source}</td>
                      <td className="py-2 pr-2">
                        <span
                          className="px-2 py-0.5 rounded text-xs font-medium"
                          style={{ backgroundColor: `${RELATIONSHIP_COLORS[e.type]}22`, color: RELATIONSHIP_COLORS[e.type] }}
                        >
                          {RELATIONSHIP_LABELS[e.type] || e.label}
                        </span>
                      </td>
                      <td className="py-2 pr-2 font-medium" style={{ color: "var(--text)" }}>{e.target}</td>
                      <td className="py-2 pr-2" style={{ color: "var(--text-muted)" }}>{e.weight}</td>
                      <td className="py-2 text-xs" style={{ color: "var(--text-muted)" }}>
                        {e.shared_scenes.slice(0, 8).join(", ")}
                        {e.shared_scenes.length > 8 ? "…" : ""}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ icon, label, value, small }: { icon: React.ReactNode; label: string; value: string | number; small?: boolean }) {
  return (
    <div className="p-3 rounded-lg text-center" style={{ backgroundColor: "var(--surface, rgba(255,255,255,0.04))" }}>
      <div className="flex items-center justify-center gap-1.5 mb-1" style={{ color: "var(--text-muted)" }}>
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className={`font-bold ${small ? "text-sm" : "text-lg"}`} style={{ color: "var(--text)" }}>{value}</p>
    </div>
  );
}
