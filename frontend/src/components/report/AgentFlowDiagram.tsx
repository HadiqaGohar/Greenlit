"use client";

import type { AgentFlowStep } from "@/lib/types";

const agentConfig: Record<
  string,
  { icon: string; label: string; color: string; borderColor: string }
> = {
  director: {
    icon: "🎬",
    label: "Director",
    color: "bg-blue-50 dark:bg-blue-900/20",
    borderColor: "border-blue-300 dark:border-blue-700",
  },
  research: {
    icon: "🔍",
    label: "Research",
    color: "bg-emerald-50 dark:bg-emerald-900/20",
    borderColor: "border-emerald-300 dark:border-emerald-700",
  },
  legal: {
    icon: "⚖️",
    label: "Legal",
    color: "bg-amber-50 dark:bg-amber-900/20",
    borderColor: "border-amber-300 dark:border-amber-700",
  },
  continuity: {
    icon: "🔗",
    label: "Continuity",
    color: "bg-purple-50 dark:bg-purple-900/20",
    borderColor: "border-purple-300 dark:border-purple-700",
  },
};

interface AgentFlowDiagramProps {
  flow: AgentFlowStep[];
}

export function AgentFlowDiagram({ flow }: AgentFlowDiagramProps) {
  if (flow.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Agent Pipeline
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Data flowing between agents
        </p>
      </div>

      <div className="flex items-center justify-between gap-2 overflow-x-auto pb-2">
        {flow.map((step, index) => {
          const config = agentConfig[step.agent] || {
            icon: "?",
            label: step.agent,
            color: "bg-gray-50 dark:bg-gray-800",
            borderColor: "border-gray-300 dark:border-gray-600",
          };

          return (
            <div key={step.agent} className="flex items-center">
              {/* Agent card */}
              <div
                className={`rounded-lg border-2 ${config.borderColor} ${config.color} p-3 min-w-[140px]`}
              >
                <div className="text-center">
                  <span className="text-2xl">{config.icon}</span>
                  <h4 className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">
                    {config.label}
                  </h4>
                </div>

                <div className="mt-2 space-y-1 text-xs text-gray-600 dark:text-gray-400">
                  {step.claims_in > 0 && (
                    <div className="flex justify-between">
                      <span>In:</span>
                      <span className="font-medium">{step.claims_in}</span>
                    </div>
                  )}
                  {step.claims_out > 0 && (
                    <div className="flex justify-between">
                      <span>Out:</span>
                      <span className="font-medium">{step.claims_out}</span>
                    </div>
                  )}
                  {step.verified > 0 && (
                    <div className="flex justify-between text-green-600 dark:text-green-400">
                      <span>✓ Verified</span>
                      <span className="font-medium">{step.verified}</span>
                    </div>
                  )}
                  {step.flagged > 0 && (
                    <div className="flex justify-between text-red-600 dark:text-red-400">
                      <span>✗ Flagged</span>
                      <span className="font-medium">{step.flagged}</span>
                    </div>
                  )}
                  {step.uncertain > 0 && (
                    <div className="flex justify-between text-yellow-600 dark:text-yellow-400">
                      <span>? Uncertain</span>
                      <span className="font-medium">{step.uncertain}</span>
                    </div>
                  )}
                  {step.issues_high > 0 && (
                    <div className="flex justify-between text-red-600 dark:text-red-400">
                      <span>High</span>
                      <span className="font-medium">{step.issues_high}</span>
                    </div>
                  )}
                  {step.issues_medium > 0 && (
                    <div className="flex justify-between text-yellow-600 dark:text-yellow-400">
                      <span>Med</span>
                      <span className="font-medium">{step.issues_medium}</span>
                    </div>
                  )}
                  {step.issues_low > 0 && (
                    <div className="flex justify-between text-blue-600 dark:text-blue-400">
                      <span>Low</span>
                      <span className="font-medium">{step.issues_low}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Arrow */}
              {index < flow.length - 1 && (
                <div className="flex items-center px-2">
                  <svg
                    width="40"
                    height="24"
                    viewBox="0 0 40 24"
                    className="text-gray-400 dark:text-gray-500"
                  >
                    <path
                      d="M0 12 L30 12 M24 6 L30 12 L24 18"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
