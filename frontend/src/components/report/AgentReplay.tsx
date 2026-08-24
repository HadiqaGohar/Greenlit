"use client";

import { useState, useEffect } from "react";
import type { AgentTimelineStep } from "@/lib/types";

const agentIcons: Record<string, string> = {
  director: "🎬",
  research: "🔍",
  legal: "⚖️",
  continuity: "🔗",
};

const agentLabels: Record<string, string> = {
  director: "Director Agent",
  research: "Research Agent",
  legal: "Legal Agent",
  continuity: "Continuity Agent",
};

const agentColors: Record<string, string> = {
  director: "from-blue-500 to-indigo-600",
  research: "from-emerald-500 to-teal-600",
  legal: "from-amber-500 to-orange-600",
  continuity: "from-purple-500 to-violet-600",
};

interface AgentReplayProps {
  timeline: AgentTimelineStep[];
  totalProcessingTime: number;
}

export function AgentReplay({ timeline, totalProcessingTime }: AgentReplayProps) {
  const [activeStep, setActiveStep] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [dots, setDots] = useState("");

  // Animate active step
  useEffect(() => {
    if (!isPlaying || timeline.length === 0) return;

    if (activeStep < timeline.length - 1) {
      const timer = setTimeout(() => {
        setActiveStep((prev) => prev + 1);
      }, 800);
      return () => clearTimeout(timer);
    } else {
      setIsPlaying(false);
    }
  }, [activeStep, isPlaying, timeline.length]);

  // Typing dots animation
  useEffect(() => {
    if (activeStep < 0 || activeStep >= timeline.length) return;
    const step = timeline[activeStep];
    if (step.status !== "running") return;

    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 400);
    return () => clearInterval(interval);
  }, [activeStep, timeline]);

  const handlePlay = () => {
    setActiveStep(0);
    setIsPlaying(true);
    setDots("");
  };

  const handleReset = () => {
    setActiveStep(-1);
    setIsPlaying(false);
    setDots("");
  };

  const getStepStatus = (index: number) => {
    if (index < activeStep) return "complete";
    if (index === activeStep) return timeline[index].status;
    return "queued";
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Agent Replay
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Watch how each agent analyzed your script
          </p>
        </div>
        <div className="flex gap-2">
          {!isPlaying && activeStep === -1 && (
            <button
              onClick={handlePlay}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
            >
              ▶ Play
            </button>
          )}
          {activeStep >= 0 && (
            <button
              onClick={handleReset}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 transition-colors"
            >
              ↺ Reset
            </button>
          )}
        </div>
      </div>

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200 dark:bg-gray-700" />

        <div className="space-y-6">
          {timeline.map((step, index) => {
            const status = getStepStatus(index);
            const isActive = index === activeStep;
            const isComplete = status === "complete";
            const isError = status === "error";

            return (
              <div
                key={step.agent}
                className={`relative flex items-start gap-4 pl-2 transition-all duration-300 ${
                  isActive ? "scale-[1.02]" : ""
                }`}
              >
                {/* Node */}
                <div className="relative z-10">
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300 ${
                      isComplete
                        ? "border-green-500 bg-green-50 dark:bg-green-900/30"
                        : isActive
                        ? `border-blue-500 bg-blue-50 dark:bg-blue-900/30 animate-pulse`
                        : isError
                        ? "border-red-500 bg-red-50 dark:bg-red-900/30"
                        : "border-gray-300 bg-gray-50 dark:border-gray-600 dark:bg-gray-800"
                    }`}
                  >
                    <span className="text-lg">{agentIcons[step.agent]}</span>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {agentLabels[step.agent]}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        step.phase === "parallel"
                          ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300"
                          : "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                      }`}
                    >
                      {step.phase}
                    </span>
                    {isComplete && (
                      <span className="text-sm text-green-600 dark:text-green-400">
                        ✓
                      </span>
                    )}
                    {isError && (
                      <span className="text-sm text-red-600 dark:text-red-400">
                        ✗
                      </span>
                    )}
                  </div>

                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {isActive && step.status === "running"
                      ? step.summary + dots
                      : step.summary}
                  </p>

                  {/* Stats */}
                  {(step.claims_count !== null || step.issues_found !== null) &&
                    isComplete && (
                      <div className="mt-2 flex gap-3">
                        {step.claims_count !== null && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {step.claims_count} claims
                          </span>
                        )}
                        {step.issues_found !== null && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {step.issues_found} issues
                          </span>
                        )}
                        {step.duration_seconds !== null && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {step.duration_seconds.toFixed(1)}s
                          </span>
                        )}
                        {step.confidence !== null && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {(step.confidence * 100).toFixed(0)}% confidence
                          </span>
                        )}
                      </div>
                    )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Total time */}
      {timeline.length > 0 && (
        <div className="mt-6 border-t border-gray-200 pt-4 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Total analysis time:{" "}
            <span className="font-medium text-gray-900 dark:text-white">
              {totalProcessingTime.toFixed(1)}s
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
