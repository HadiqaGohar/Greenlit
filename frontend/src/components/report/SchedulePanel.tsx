"use client";

import { useState } from "react";

interface ScheduleScene {
  scene_number: number;
  title: string;
  location: string;
  int_ext: string;
  time_of_day: string;
  characters: string[];
  page_eighths: number;
  page_count: string;
  complexity: number;
  strip_color: string;
  dialogue_count: number;
  action_line_count: number;
}

interface ShootDay {
  day_number: number;
  scenes: ScheduleScene[];
  total_page_eighths: number;
  total_page_count: string;
  locations: string[];
  company_moves: number;
  cast_required: string[];
  is_night_shoot: boolean;
  estimated_hours: number;
  scene_count: number;
}

interface ScheduleResponse {
  schedule_id: string;
  report_id: string;
  success: boolean;
  shoot_days: ShootDay[];
  total_shoot_days: number;
  contingency_days: number;
  total_pages: string;
  total_pages_eighths: number;
  company_moves_total: number;
  cast_schedule: Record<string, Array<{ day: number; status: string }>>;
  location_summary: Array<{
    location: string;
    scene_count: number;
    scene_numbers: number[];
    total_pages: string;
    characters: string[];
    has_day: boolean;
    has_night: boolean;
  }>;
  optimization_notes: string[];
  pages_per_day_target: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

interface SchedulePanelProps {
  reportId: string;
}

const STRIP_COLORS: Record<string, string> = {
  white: "bg-white border-gray-300",
  yellow: "bg-yellow-50 border-yellow-300",
  blue: "bg-blue-50 border-blue-300",
  green: "bg-green-50 border-green-300",
};

const STRIP_DARK: Record<string, string> = {
  white: "dark:bg-gray-800 dark:border-gray-600",
  yellow: "dark:bg-yellow-900/20 dark:border-yellow-700",
  blue: "dark:bg-blue-900/20 dark:border-blue-700",
  green: "dark:bg-green-900/20 dark:border-green-700",
};

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  SW: { label: "SW", color: "bg-green-500 text-white" },
  W: { label: "W", color: "bg-blue-500 text-white" },
  WF: { label: "WF", color: "bg-green-500 text-white" },
  SWF: { label: "SWF", color: "bg-green-600 text-white" },
  H: { label: "H", color: "bg-amber-400 text-amber-900" },
};

type ViewMode = "days" | "stripboard" | "cast" | "locations";

export function SchedulePanel({ reportId }: SchedulePanelProps) {
  const [schedule, setSchedule] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("days");
  const [expandedDay, setExpandedDay] = useState<number | null>(null);

  const generateSchedule = async () => {
    setLoading(true);
    setError(null);
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_URL}/api/schedule/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to generate schedule");
      }
      setSchedule(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate schedule");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            📅 Production Schedule
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            AI-optimized day-by-day shooting schedule
          </p>
        </div>
        {!schedule && !loading && (
          <button
            onClick={generateSchedule}
            className="rounded-lg bg-gradient-to-r from-amber-600 to-orange-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:from-amber-700 hover:to-orange-700 transition-all"
          >
            📋 Generate Schedule
          </button>
        )}
        {schedule && (
          <button
            onClick={generateSchedule}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
          >
            🔄 Regenerate
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-12 text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-amber-200 border-t-amber-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            Optimizing shooting schedule...
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Grouping locations, clustering cast, balancing pages
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          <button onClick={generateSchedule} className="mt-2 text-xs font-medium text-red-600 hover:text-red-800 dark:text-red-400">
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      {schedule && !loading && (
        <div>
          {/* Stats */}
          <div className="mb-4 flex flex-wrap items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              🎬 <strong>{schedule.total_shoot_days}</strong> shoot days
            </span>
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              📄 {schedule.total_pages} pages
            </span>
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              🚚 {schedule.company_moves_total} company moves
            </span>
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              🛡️ +{schedule.contingency_days} contingency
            </span>
            <span className="text-gray-400">
              ⚡ {schedule.processing_time.toFixed(1)}s
            </span>
          </div>

          {/* View Tabs */}
          <div className="mb-4 flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
            {(["days", "stripboard", "cast", "locations"] as ViewMode[]).map((v) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  view === v
                    ? "bg-white text-gray-900 shadow dark:bg-gray-700 dark:text-white"
                    : "text-gray-500 hover:text-gray-700 dark:text-gray-400"
                }`}
              >
                {v === "days" && "📅 Day by Day"}
                {v === "stripboard" && "🎯 Stripboard"}
                {v === "cast" && "🎭 Cast Grid"}
                {v === "locations" && "📍 Locations"}
              </button>
            ))}
          </div>

          {/* Day by Day View */}
          {view === "days" && (
            <div className="space-y-3">
              {schedule.shoot_days.map((day) => (
                <DayCard
                  key={day.day_number}
                  day={day}
                  expanded={expandedDay === day.day_number}
                  onToggle={() => setExpandedDay(expandedDay === day.day_number ? null : day.day_number)}
                />
              ))}
            </div>
          )}

          {/* Stripboard View */}
          {view === "stripboard" && (
            <div className="space-y-1">
              {schedule.shoot_days.map((day) => (
                <div key={day.day_number}>
                  <div className="flex items-center gap-2 border-b border-gray-200 py-1.5 dark:border-gray-700">
                    <span className="w-16 text-xs font-bold text-gray-500 dark:text-gray-400">
                      DAY {day.day_number}
                    </span>
                    <div className="flex flex-1 gap-1 overflow-x-auto">
                      {day.scenes.map((scene) => (
                        <div
                          key={scene.scene_number}
                          className={`flex-shrink-0 rounded border px-2 py-1 text-xs ${
                            STRIP_COLORS[scene.strip_color] || STRIP_COLORS.white
                          } ${STRIP_DARK[scene.strip_color] || STRIP_DARK.white}`}
                        >
                          <span className="font-bold">Sc {scene.scene_number}</span>
                          <span className="ml-1 text-gray-600 dark:text-gray-400">
                            {scene.page_count}
                          </span>
                          <span className="ml-1 text-gray-400 dark:text-gray-500">
                            {scene.characters.slice(0, 2).join(", ")}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Cast Grid (Day Out of Days) */}
          {view === "cast" && (
            <CastGrid castSchedule={schedule.cast_schedule} totalDays={schedule.total_shoot_days} />
          )}

          {/* Locations View */}
          {view === "locations" && (
            <LocationsView locationSummary={schedule.location_summary} />
          )}

          {/* Optimization Notes */}
          {schedule.optimization_notes.length > 0 && (
            <div className="mt-6 rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
              <h4 className="mb-2 text-sm font-semibold text-blue-800 dark:text-blue-200">
                💡 Optimization Notes
              </h4>
              <ul className="space-y-1">
                {schedule.optimization_notes.map((note, i) => (
                  <li key={i} className="text-xs text-blue-700 dark:text-blue-300">
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DayCard({ day, expanded, onToggle }: { day: ShootDay; expanded: boolean; onToggle: () => void }) {
  const moveLabel = day.company_moves === 0
    ? "No moves"
    : day.company_moves === 1
    ? "1 company move"
    : `${day.company_moves} company moves`;

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-4 p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div className={`flex h-12 w-12 items-center justify-center rounded-lg font-bold text-sm ${
          day.is_night_shoot
            ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300"
            : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
        }`}>
          {day.day_number}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
              Day {day.day_number}
            </h4>
            {day.is_night_shoot && (
              <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300">
                NIGHT
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {day.scene_count} scenes · {day.total_page_count} pages · {moveLabel} · ~{day.estimated_hours}h
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>📍 {day.locations.length}</span>
          <span>🎭 {day.cast_required.length}</span>
          <svg className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 dark:border-gray-700 dark:bg-gray-800/50">
          <div className="mb-2 text-xs text-gray-500 dark:text-gray-400">
            📍 Locations: {day.locations.join(", ")}
          </div>
          <div className="space-y-1">
            {day.scenes.map((scene) => (
              <div
                key={scene.scene_number}
                className={`flex items-center gap-3 rounded border px-3 py-2 text-sm ${
                  STRIP_COLORS[scene.strip_color] || STRIP_COLORS.white
                } ${STRIP_DARK[scene.strip_color] || STRIP_DARK.white}`}
              >
                <span className="font-bold text-gray-900 dark:text-white w-12">
                  Sc {scene.scene_number}
                </span>
                <span className="flex-1 truncate text-gray-700 dark:text-gray-300">
                  {scene.title}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 w-12 text-right">
                  {scene.page_count}
                </span>
                <span className="text-xs text-gray-400 dark:text-gray-500 w-24 truncate">
                  {scene.characters.join(", ")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function CastGrid({ castSchedule, totalDays }: { castSchedule: Record<string, Array<{ day: number; status: string }>>; totalDays: number }) {
  const characters = Object.keys(castSchedule).sort();
  const days = Array.from({ length: totalDays }, (_, i) => i + 1);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="sticky left-0 z-10 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-700 dark:bg-gray-800 dark:text-gray-300">
              Cast Member
            </th>
            {days.map((d) => (
              <th key={d} className="px-2 py-2 text-center font-medium text-gray-500 dark:text-gray-400">
                D{d}
              </th>
            ))}
            <th className="px-3 py-2 text-center font-medium text-gray-500 dark:text-gray-400">
              Days
            </th>
          </tr>
        </thead>
        <tbody>
          {characters.map((char) => {
            const entries = castSchedule[char];
            const statusMap = new Map(entries.map((e) => [e.day, e.status]));
            const workDays = entries.filter((e) => e.status !== "H").length;
            const holdDays = entries.filter((e) => e.status === "H").length;

            return (
              <tr key={char} className="border-b border-gray-100 dark:border-gray-800">
                <td className="sticky left-0 z-10 bg-white px-3 py-2 font-medium text-gray-900 dark:bg-gray-900 dark:text-white whitespace-nowrap">
                  {char}
                </td>
                {days.map((d) => {
                  const status = statusMap.get(d);
                  const info = status ? STATUS_LABELS[status] : null;
                  return (
                    <td key={d} className="px-2 py-2 text-center">
                      {info ? (
                        <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-bold ${info.color}`}>
                          {info.label}
                        </span>
                      ) : (
                        <span className="text-gray-300 dark:text-gray-600">·</span>
                      )}
                    </td>
                  );
                })}
                <td className="px-3 py-2 text-center text-gray-500 dark:text-gray-400">
                  {workDays}w{holdDays > 0 ? ` / ${holdDays}h` : ""}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <div className="mt-3 flex flex-wrap gap-3 text-[10px] text-gray-500 dark:text-gray-400">
        <span><span className="inline-block rounded bg-green-500 px-1 py-0.5 text-white">SW</span> Start/Work</span>
        <span><span className="inline-block rounded bg-blue-500 px-1 py-0.5 text-white">W</span> Work</span>
        <span><span className="inline-block rounded bg-green-500 px-1 py-0.5 text-white">WF</span> Work/Finish</span>
        <span><span className="inline-block rounded bg-green-600 px-1 py-0.5 text-white">SWF</span> Start/Work/Finish</span>
        <span><span className="inline-block rounded bg-amber-400 px-1 py-0.5 text-amber-900">H</span> Hold</span>
      </div>
    </div>
  );
}

function LocationsView({ locationSummary }: { locationSummary: ScheduleResponse["location_summary"] }) {
  return (
    <div className="space-y-3">
      {locationSummary.map((loc) => (
        <div key={loc.location} className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold text-gray-900 dark:text-white">{loc.location}</h4>
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              {loc.has_day && <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300">DAY</span>}
              {loc.has_night && <span className="rounded bg-blue-100 px-1.5 py-0.5 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">NIGHT</span>}
            </div>
          </div>
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
            <span>{loc.scene_count} scenes</span>
            <span>{loc.total_pages} pages</span>
            <span>Scenes: {loc.scene_numbers.join(", ")}</span>
          </div>
          <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
            Cast: {loc.characters.join(", ")}
          </div>
        </div>
      ))}
    </div>
  );
}
