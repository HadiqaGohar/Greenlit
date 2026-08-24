"use client";

import { useState } from "react";

interface Scene {
  scene_number: number;
  title: string;
  location: string;
  time_of_day: string;
  characters_present: string[];
  risk_score: number;
  estimated_cost: number;
  production_notes: string[];
  required_clearances: string[];
}

interface SceneBreakdownDashboardProps {
  scenes: Scene[];
}

const riskColors: Record<string, string> = {
  low: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
  medium: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300",
  high: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
};

function getRiskLevel(score: number): string {
  if (score < 30) return "low";
  if (score < 70) return "medium";
  return "high";
}

export function SceneBreakdownDashboard({ scenes }: SceneBreakdownDashboardProps) {
  const [selectedScene, setSelectedScene] = useState<number | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  if (scenes.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Scene Breakdown
        </h3>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          No scene data available. Analyze a script to see scene breakdown.
        </p>
      </div>
    );
  }

  const totalCost = scenes.reduce((sum, s) => sum + s.estimated_cost, 0);
  const avgRisk = scenes.reduce((sum, s) => sum + s.risk_score, 0) / scenes.length;
  const highRiskScenes = scenes.filter((s) => s.risk_score >= 70).length;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Scene Breakdown
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {scenes.length} scenes analyzed
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode("grid")}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              viewMode === "grid"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            Grid
          </button>
          <button
            onClick={() => setViewMode("list")}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              viewMode === "list"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300"
            }`}
          >
            List
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {scenes.length}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Total Scenes</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <p className="text-2xl font-bold text-amber-600">
            ${totalCost.toLocaleString()}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Est. Total Cost</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
          <p className="text-2xl font-bold text-red-600">{highRiskScenes}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">High Risk Scenes</p>
        </div>
      </div>

      {/* Scene Cards */}
      <div
        className={
          viewMode === "grid"
            ? "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
            : "space-y-2"
        }
      >
        {scenes.map((scene) => {
          const riskLevel = getRiskLevel(scene.risk_score);
          const isSelected = selectedScene === scene.scene_number;

          return (
            <div
              key={scene.scene_number}
              onClick={() => setSelectedScene(isSelected ? null : scene.scene_number)}
              className={`cursor-pointer rounded-lg border p-4 transition-all ${
                isSelected
                  ? "border-blue-500 ring-2 ring-blue-200 dark:ring-blue-800"
                  : "border-gray-200 hover:border-gray-300 dark:border-gray-700 dark:hover:border-gray-600"
              }`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                    Scene {scene.scene_number}
                  </span>
                  <h4 className="mt-1 font-medium text-gray-900 dark:text-white">
                    {scene.title}
                  </h4>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {scene.location} · {scene.time_of_day}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${riskColors[riskLevel]}`}
                >
                  {scene.risk_score.toFixed(0)}
                </span>
              </div>

              {/* Characters */}
              <div className="mt-3 flex flex-wrap gap-1">
                {scene.characters_present.slice(0, 3).map((char) => (
                  <span
                    key={char}
                    className="rounded bg-blue-100 px-1.5 py-0.5 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                  >
                    {char}
                  </span>
                ))}
                {scene.characters_present.length > 3 && (
                  <span className="text-xs text-gray-400">
                    +{scene.characters_present.length - 3}
                  </span>
                )}
              </div>

              {/* Cost */}
              <div className="mt-2 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>Est. ${scene.estimated_cost.toLocaleString()}</span>
                {scene.required_clearances.length > 0 && (
                  <span className="text-amber-600">
                    {scene.required_clearances.length} clearances
                  </span>
                )}
              </div>

              {/* Expanded Details */}
              {isSelected && (
                <div className="mt-4 border-t border-gray-200 pt-3 dark:border-gray-700">
                  <h5 className="mb-2 text-xs font-medium text-gray-700 dark:text-gray-300">
                    Production Notes:
                  </h5>
                  <ul className="space-y-1">
                    {scene.production_notes.map((note, i) => (
                      <li
                        key={i}
                        className="text-xs text-gray-600 dark:text-gray-400"
                      >
                        • {note}
                      </li>
                    ))}
                  </ul>
                  {scene.required_clearances.length > 0 && (
                    <>
                      <h5 className="mb-2 mt-3 text-xs font-medium text-gray-700 dark:text-gray-300">
                        Required Clearances:
                      </h5>
                      <div className="flex flex-wrap gap-1">
                        {scene.required_clearances.map((clearance, i) => (
                          <span
                            key={i}
                            className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                          >
                            {clearance}
                          </span>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
