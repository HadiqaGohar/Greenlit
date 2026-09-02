"use client";

import { useState, useEffect } from "react";

interface SceneRisk {
  scene_number: number;
  title: string;
  location: string;
  time_of_day: string;
  risk_score: number;
  risk_level: "low" | "medium" | "high" | "critical";
  risk_factors: string[];
  legal_issues: Array<{ description?: string; type?: string; severity?: string }>;
  continuity_issues: Array<{ description?: string }>;
  research_flags: Array<{ text?: string; verdict?: string }>;
  estimated_cost: number;
  text_start: number;
  text_end: number;
  reasoning: string;
}

interface SceneRiskResponse {
  report_id: string;
  total_scenes: number;
  overall_risk_score: number;
  scenes: SceneRisk[];
  risk_distribution: Record<string, number>;
}

interface RiskHeatmapProps {
  reportId: string;
  scriptText: string;
}

const riskColors: Record<string, { bg: string; border: string; text: string }> = {
  low: { bg: "bg-green-100", border: "border-green-400", text: "text-green-800" },
  medium: { bg: "bg-yellow-100", border: "border-yellow-400", text: "text-yellow-800" },
  high: { bg: "bg-orange-100", border: "border-orange-400", text: "text-orange-800" },
  critical: { bg: "bg-red-100", border: "border-red-400", text: "text-red-800" },
};

const riskHighlightColors: Record<string, string> = {
  low: "bg-green-200/50",
  medium: "bg-yellow-200/50",
  high: "bg-orange-200/50",
  critical: "bg-red-200/50",
};

export function RiskHeatmap({ reportId, scriptText }: RiskHeatmapProps) {
  const [sceneRiskData, setSceneRiskData] = useState<SceneRiskResponse | null>(
    null
  );
  const [selectedScene, setSelectedScene] = useState<SceneRisk | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchSceneRiskData();
  }, [reportId]);

  const fetchSceneRiskData = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `${
          process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
        }/api/scene-risk/${reportId}`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch scene risk data");
      }

      const data = await response.json();
      setSceneRiskData(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load risk data"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getRiskColor = (level: string) => riskColors[level] || riskColors.low;
  const getHighlightColor = (level: string) =>
    riskHighlightColors[level] || riskHighlightColors.low;

  const renderHighlightedScript = () => {
    if (!sceneRiskData || !sceneRiskData.scenes.length) {
      return (
        <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          {scriptText}
        </pre>
      );
    }

    // Sort scenes by text_start
    const sortedScenes = [...sceneRiskData.scenes].sort(
      (a, b) => a.text_start - b.text_start
    );

    const parts: JSX.Element[] = [];
    let lastEnd = 0;

    sortedScenes.forEach((scene, index) => {
      // Add text before this scene
      if (scene.text_start > lastEnd) {
        parts.push(
          <span key={`pre-${index}`} className="text-gray-700 dark:text-gray-300">
            {scriptText.slice(lastEnd, scene.text_start)}
          </span>
        );
      }

      // Add highlighted scene text
      const sceneText = scriptText.slice(scene.text_start, scene.text_end);
      if (sceneText) {
        const isSelected = selectedScene?.scene_number === scene.scene_number;
        parts.push(
          <span
            key={`scene-${scene.scene_number}`}
            className={`${getHighlightColor(scene.risk_level)} ${
              isSelected ? "ring-2 ring-blue-500 ring-offset-1" : ""
            } cursor-pointer transition-all hover:brightness-90`}
            onClick={() => setSelectedScene(scene)}
            title={`Scene ${scene.scene_number}: ${scene.risk_level} risk`}
          >
            {sceneText}
          </span>
        );
      }

      lastEnd = scene.text_end;
    });

    // Add remaining text
    if (lastEnd < scriptText.length) {
      parts.push(
        <span key="post" className="text-gray-700 dark:text-gray-300">
          {scriptText.slice(lastEnd)}
        </span>
      );
    }

    return (
      <pre className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
        {parts}
      </pre>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-xl">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Loading risk heatmap...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-800 rounded-xl">
        <div className="text-center text-red-600">
          <p className="font-medium">Error loading risk data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Risk Distribution Bar */}
      {sceneRiskData && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Risk Heatmap
            </h3>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {sceneRiskData.total_scenes} scenes analyzed
            </span>
          </div>

          {/* Risk Distribution */}
          <div className="flex gap-2 mb-4">
            {Object.entries(sceneRiskData.risk_distribution).map(
              ([level, count]) => (
                <div
                  key={level}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${getRiskColor(level).bg}`}
                >
                  <span
                    className={`w-3 h-3 rounded-full ${
                      level === "critical"
                        ? "bg-red-500"
                        : level === "high"
                        ? "bg-orange-500"
                        : level === "medium"
                        ? "bg-yellow-500"
                        : "bg-green-500"
                    }`}
                  />
                  <span
                    className={`text-sm font-medium ${getRiskColor(level).text}`}
                  >
                    {count} {level}
                  </span>
                </div>
              )
            )}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
            <span>
              <span className="inline-block w-4 h-2 bg-green-200 rounded mr-1" />
              Low Risk
            </span>
            <span>
              <span className="inline-block w-4 h-2 bg-yellow-200 rounded mr-1" />
              Medium Risk
            </span>
            <span>
              <span className="inline-block w-4 h-2 bg-orange-200 rounded mr-1" />
              High Risk
            </span>
            <span>
              <span className="inline-block w-4 h-2 bg-red-200 rounded mr-1" />
              Critical Risk
            </span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Script Panel */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 max-h-[600px] overflow-y-auto">
            <h4 className="font-medium text-gray-900 dark:text-white mb-3">
              Annotated Script
            </h4>
            {renderHighlightedScript()}
          </div>
        </div>

        {/* Scene Details Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4 sticky top-6">
            {selectedScene ? (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white">
                    Scene {selectedScene.scene_number}
                  </h4>
                  <button
                    onClick={() => setSelectedScene(null)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12"
                      />
                    </svg>
                  </button>
                </div>

                <div className="space-y-4">
                  {/* Risk Score */}
                  <div
                    className={`p-3 rounded-lg ${getRiskColor(selectedScene.risk_level).bg}`}
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={`font-medium ${getRiskColor(selectedScene.risk_level).text}`}
                      >
                        {selectedScene.risk_level.toUpperCase()} RISK
                      </span>
                      <span
                        className={`text-2xl font-bold ${getRiskColor(selectedScene.risk_level).text}`}
                      >
                        {selectedScene.risk_score.toFixed(0)}
                      </span>
                    </div>
                  </div>

                  {/* Scene Info */}
                  <div className="text-sm space-y-2">
                    <p>
                      <span className="text-gray-500 dark:text-gray-400">
                        Title:
                      </span>{" "}
                      <span className="text-gray-900 dark:text-white">
                        {selectedScene.title}
                      </span>
                    </p>
                    <p>
                      <span className="text-gray-500 dark:text-gray-400">
                        Location:
                      </span>{" "}
                      <span className="text-gray-900 dark:text-white">
                        {selectedScene.location}
                      </span>
                    </p>
                    <p>
                      <span className="text-gray-500 dark:text-gray-400">
                        Time:
                      </span>{" "}
                      <span className="text-gray-900 dark:text-white">
                        {selectedScene.time_of_day}
                      </span>
                    </p>
                  </div>

                  {/* Risk Factors */}
                  {selectedScene.risk_factors.length > 0 && (
                    <div>
                      <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                        Risk Factors
                      </h5>
                      <ul className="text-sm space-y-1">
                        {selectedScene.risk_factors.map((factor, i) => (
                          <li
                            key={i}
                            className="text-gray-600 dark:text-gray-300 flex items-start gap-2"
                          >
                            <span className="text-red-500 mt-1">•</span>
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Legal Issues */}
                  {selectedScene.legal_issues.length > 0 && (
                    <div>
                      <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                        Legal Issues
                      </h5>
                      <ul className="text-sm space-y-1">
                        {selectedScene.legal_issues.map((issue, i) => (
                          <li
                            key={i}
                            className="text-gray-600 dark:text-gray-300 flex items-start gap-2"
                          >
                            <span className="text-orange-500 mt-1">⚖️</span>
                            {issue.description || issue.type || "Legal issue"}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Continuity Issues */}
                  {selectedScene.continuity_issues.length > 0 && (
                    <div>
                      <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                        Continuity Issues
                      </h5>
                      <ul className="text-sm space-y-1">
                        {selectedScene.continuity_issues.map((issue, i) => (
                          <li
                            key={i}
                            className="text-gray-600 dark:text-gray-300 flex items-start gap-2"
                          >
                            <span className="text-yellow-500 mt-1">🔄</span>
                            {issue.description || "Continuity issue"}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Research Flags */}
                  {selectedScene.research_flags.length > 0 && (
                    <div>
                      <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                        Research Flags
                      </h5>
                      <ul className="text-sm space-y-1">
                        {selectedScene.research_flags.map((flag, i) => (
                          <li
                            key={i}
                            className="text-gray-600 dark:text-gray-300 flex items-start gap-2"
                          >
                            <span className="text-red-500 mt-1">🔍</span>
                            {flag.text || "Flagged claim"}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* AI Reasoning */}
                  <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
                    <h5 className="font-medium text-gray-900 dark:text-white mb-2">
                      AI Reasoning
                    </h5>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {selectedScene.reasoning}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 mb-3">
                  <span className="text-2xl">👆</span>
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Click on a highlighted scene to see detailed risk analysis
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Scene Risk Cards */}
      {sceneRiskData && sceneRiskData.scenes.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-4">
            Scene Risk Overview
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {sceneRiskData.scenes.map((scene) => (
              <button
                key={scene.scene_number}
                onClick={() => setSelectedScene(scene)}
                className={`p-3 rounded-lg border text-left transition-all hover:shadow-md ${
                  selectedScene?.scene_number === scene.scene_number
                    ? "ring-2 ring-blue-500"
                    : ""
                } ${getRiskColor(scene.risk_level).bg} ${
                  getRiskColor(scene.risk_level).border
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className={`font-medium ${getRiskColor(scene.risk_level).text}`}
                  >
                    Scene {scene.scene_number}
                  </span>
                  <span
                    className={`text-lg font-bold ${getRiskColor(scene.risk_level).text}`}
                  >
                    {scene.risk_score.toFixed(0)}
                  </span>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                  {scene.title}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
