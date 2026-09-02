"use client";

import { useCallback, useState, useRef } from "react";

import { analyzeScript, ApiError } from "@/lib/api";
import type { AnalyzeResponse } from "@/lib/types";

interface AgentProgress {
  name: string;
  status: "queued" | "running" | "complete" | "error";
  progress: number;
}

interface UseAnalysisState {
  isLoading: boolean;
  error: string | null;
  report: AnalyzeResponse | null;
  progress: number;
  status: string;
  agentStatus: Record<string, AgentProgress>;
  estimatedTimeRemaining: number | null;
}

export function useAnalysis(userId?: string) {
  const [state, setState] = useState<UseAnalysisState>({
    isLoading: false,
    error: null,
    report: null,
    progress: 0,
    status: "",
    agentStatus: {},
    estimatedTimeRemaining: null,
  });
  const startTimeRef = useRef<number>(0);
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const simulateProgress = useCallback(() => {
    const agents = ["director", "research", "legal", "continuity"];
    let currentAgent = 0;
    let progress = 5;

    setState((prev) => ({
      ...prev,
      progress: 5,
      status: "Initializing analysis...",
      agentStatus: Object.fromEntries(
        agents.map((a) => [a, { name: a, status: "queued", progress: 0 }]),
      ),
    }));

    progressIntervalRef.current = setInterval(() => {
      setState((prev) => {
        const agentName = agents[currentAgent];
        const newAgentStatus = { ...prev.agentStatus };
        const elapsed = (Date.now() - startTimeRef.current) / 1000;

        // Update current agent
        if (currentAgent < agents.length) {
          const agentProgress = Math.min(
            100,
            (prev.agentStatus[agentName]?.progress ?? 0) + Math.random() * 15 + 5,
          );
          newAgentStatus[agentName] = {
            name: agentName,
            status: agentProgress >= 100 ? "complete" : "running",
            progress: agentProgress,
          };

          // Move to next agent when current is done
          if (agentProgress >= 100) {
            currentAgent++;
            if (currentAgent < agents.length) {
              newAgentStatus[agents[currentAgent]] = {
                name: agents[currentAgent],
                status: "running",
                progress: 0,
              };
            }
          }
        }

        progress = Math.min(95, progress + Math.random() * 8 + 2);
        const completedAgents = Object.values(newAgentStatus).filter(
          (a) => a.status === "complete",
        ).length;
        const estimatedTotal = elapsed / (progress / 100);
        const remaining = Math.max(0, estimatedTotal - elapsed);

        const statusMessages = [
          "Extracting claims from script...",
          "Researching factual claims...",
          "Analyzing legal clearance...",
          "Checking continuity...",
          "Aggregating results...",
        ];
        const statusIndex = Math.min(
          Math.floor((progress / 100) * statusMessages.length),
          statusMessages.length - 1,
        );

        if (progress >= 95 || completedAgents >= agents.length) {
          if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
        }

        return {
          ...prev,
          progress,
          status: statusMessages[statusIndex],
          agentStatus: newAgentStatus,
          estimatedTimeRemaining: remaining,
        };
      });
    }, 800);
  }, []);

  const analyze = useCallback(
    async (scriptText: string) => {
      startTimeRef.current = Date.now();
      setState({
        isLoading: true,
        error: null,
        report: null,
        progress: 0,
        status: "Starting analysis...",
        agentStatus: {},
        estimatedTimeRemaining: null,
      });

      simulateProgress();

      try {
        const report = await analyzeScript({ script_text: scriptText }, userId);
        if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
        setState({
          isLoading: false,
          error: null,
          report,
          progress: 100,
          status: "Analysis complete!",
          agentStatus: Object.fromEntries(
            Object.entries(report.agent_results ?? {}).map(([name, r]: [string, { success: boolean }]) => [
              name,
              {
                name,
                status: r.success ? "complete" : "error",
                progress: 100,
              },
            ]),
          ),
          estimatedTimeRemaining: 0,
        });
        return report;
      } catch (err) {
        if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
        const message =
          err instanceof ApiError
            ? err.message
            : "Something went wrong. Please try again.";
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: message,
          report: null,
          status: "Analysis failed",
        }));
        return null;
      }
    },
    [simulateProgress, userId],
  );

  const reset = useCallback(() => {
    if (progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    setState({
      isLoading: false,
      error: null,
      report: null,
      progress: 0,
      status: "",
      agentStatus: {},
      estimatedTimeRemaining: null,
    });
  }, []);

  return { ...state, analyze, reset };
}
