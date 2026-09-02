"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useSpring, useMotionValueEvent } from "framer-motion";
import {
  getRiskColor,
  getAgentIcon,
  getAgentColor,
} from "@/lib/utils";
import {
  getRiskDetail,
  getSceneRiskData,
  RiskDetailResponse,
  SceneRiskData,
} from "@/lib/api";
import {
  AgentFlowStep,
  AgentType,
  ProductionIssue,
  ReadinessScore,
  Suggestion,
} from "@/lib/types";
import { RiskGauge } from "./RiskGauge";
import { PieChart, PieChartSlice } from "../charts/PieChart";
import { BarChart, BarChartData } from "../charts/BarChart";
import { TrendLine } from "../charts/TrendLine";

interface RiskDashboardProps {
  reportId: string;
}

const AnimatedNumber = ({ value }: { value: number }) => {
  const spring = useSpring(0, { stiffness: 100, damping: 30 });
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    spring.set(value);
  }, [spring, value]);

  useMotionValueEvent(spring, "change", (latest) => {
    setDisplayValue(Math.round(latest));
  });

  return (
    <motion.span className="font-bold text-2xl" style={{ color: "var(--text)" }}>
      {displayValue}
    </motion.span>
  );
};

const ReadinessBars = ({ scores }: { scores: ReadinessScore }) => {
  const data = [
    { label: "Legal Clearance", score: scores.legal_clearance, color: "var(--legal-color, #60a5fa)" },
    { label: "Historical Accuracy", score: scores.historical_accuracy, color: "var(--research-color, #34d399)" },
    { label: "Continuity", score: scores.continuity, color: "var(--continuity-color, #fcd34d)" },
    { label: "Budget Feasibility", score: scores.budget_feasibility, color: "var(--schedule-color, #a78bfa)" },
  ];

  return (
    <div className="space-y-3">
      <h4 className="text-lg font-semibold mb-2" style={{ color: "var(--text)" }}>
        Readiness Scores
      </h4>
      {data.map((item, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-sm w-36 flex-shrink-0" style={{ color: "var(--text-muted)" }}>
            {item.label}
          </span>
          <div className="relative h-2 flex-grow rounded-full bg-gray-200 dark:bg-gray-700">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${item.score}%` }}
              transition={{ duration: 0.8, delay: i * 0.1 }}
              className="absolute inset-y-0 left-0 rounded-full"
              style={{ backgroundColor: item.color }}
            />
          </div>
          <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
            {Math.round(item.score)}%
          </span>
        </div>
      ))}
      <div className="flex justify-end mt-4">
        <span
          className={`rounded-full px-3 py-1 text-sm font-semibold`}
          style={{
            backgroundColor: getRiskColor(scores.overall) + "20",
            color: getRiskColor(scores.overall),
          }}
        >
          Overall Grade: {scores.grade}
        </span>
      </div>
    </div>
  );
};

const CriticalIssuesFeed = ({
  issues,
  suggestions,
}: {
  issues: ProductionIssue[];
  suggestions: Suggestion[];
}) => {
  const mergedIssues = issues.map((issue) => ({
    ...issue,
    suggested_text:
      suggestions.find((s) => s.issue_id === issue.description)?.suggested_text ||
      issue.suggested_action,
  }));

  const issueSeverityColors: Record<string, string> = {
    critical: "var(--flagged)",
    high: "var(--warning)",
    medium: "var(--accent)",
    low: "var(--verified)",
  };

  return (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
        Critical Issues & Recommendations
      </h4>
      <AnimatePresence>
        {mergedIssues.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-gray-500 dark:text-gray-400 py-4"
          >
            No critical issues found. Great job!
          </motion.div>
        ) : (
          mergedIssues.map((issue, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ delay: i * 0.05 }}
              className="flex items-start gap-3 p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800"
            >
              <span
                className="flex-shrink-0 text-xl"
                style={{ color: issueSeverityColors[issue.severity] || "var(--text-muted)" }}
              >
                {issue.severity === "critical" && "🚨"}
                {issue.severity === "high" && "⚠️"}
                {issue.severity === "medium" && "🔶"}
                {issue.severity === "low" && "✅"}
              </span>
              <div className="flex-grow">
                <p className="font-medium" style={{ color: "var(--text)" }}>
                  {issue.description}
                </p>
                {issue.suggested_text && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    <span className="font-medium">Action:</span> {issue.suggested_text}
                  </p>
                )}
              </div>
            </motion.div>
          ))
        )}
      </AnimatePresence>
    </div>
  );
};

const AgentConfidenceBars = ({ agentFlow }: { agentFlow: AgentFlowStep[] }) => {
  const agentConfidenceData = agentFlow.map((flow) => {
    const total = flow.claims_in || 1;
    const confidence = (flow.verified / total) * 100; // Simplified confidence calculation
    return {
      agent: flow.agent,
      confidence: isNaN(confidence) ? 0 : confidence,
    };
  });

  return (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
        Agent Confidence
      </h4>
      {agentConfidenceData.map((item, i) => (
        <div key={item.agent} className="flex items-center gap-3">
          <span className="text-xl flex-shrink-0" style={{ color: "var(--text)" }}>
            {getAgentIcon(item.agent as AgentType)}
          </span>
          <span className="text-sm w-24 flex-shrink-0" style={{ color: "var(--text-muted)" }}>
            {item.agent}
          </span>
          <div className="relative h-2 flex-grow rounded-full bg-gray-200 dark:bg-gray-700">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${item.confidence}%` }}
              transition={{ duration: 0.8, delay: i * 0.1 }}
              className="absolute inset-y-0 left-0 rounded-full"
              style={{ backgroundColor: getAgentColor(item.agent as AgentType) }}
            />
          </div>
          <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
            {Math.round(item.confidence)}%
          </span>
        </div>
      ))}
    </div>
  );
};

export function RiskDashboard({ reportId }: RiskDashboardProps) {
  const [riskDetail, setRiskDetail] = useState<RiskDetailResponse | null>(null);
  const [sceneRiskData, setSceneRiskData] = useState<SceneRiskData[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const detail = await getRiskDetail(reportId);
        setRiskDetail(detail);

        const sceneData = await getSceneRiskData(reportId);
        setSceneRiskData(sceneData.scenes);
      } catch (err) {
        console.error("Failed to fetch risk dashboard data:", err);
        setError("Failed to load risk dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [reportId]);

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-500 dark:text-red-400 py-8">{error}</div>
    );
  }

  if (!riskDetail) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400 py-8">
        No risk data available for this report.
      </div>
    );
  }

  const { risk_assessment, critical_issues, agent_flow, suggestions } = riskDetail;
  const { overall_risk_score, risk_level } = risk_assessment;

  // Prepare Pie Chart Data (Risk by Category)
  const riskCategoryData: PieChartSlice[] = critical_issues.reduce(
    (acc: PieChartSlice[], issue: ProductionIssue) => {
      const existing = acc.find((item) => item.label === issue.type);
      if (existing) {
        existing.value += 1;
      } else {
        acc.push({ label: issue.type, value: 1, color: getAgentColor(issue.type as AgentType) });
      }
      return acc;
    },
    [] as PieChartSlice[]
  );

  // Prepare Bar Chart Data (Issues by Severity)
  const severityCounts: Record<string, number> = critical_issues.reduce(
    (acc: Record<string, number>, issue: ProductionIssue) => {
      acc[issue.severity] = (acc[issue.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const severityBarChartData: BarChartData = {
    labels: ["critical", "high", "medium", "low"],
    datasets: [
      {
        label: "Severity",
        data: ["critical", "high", "medium", "low"].map((s) => severityCounts[s] || 0),
        color: undefined, // Colors handled by internal logic of BarChart or custom here
      },
    ],
  };

  // Prepare TrendLine Data (Scene Risk Timeline)
  const sceneLabels = sceneRiskData?.map((scene) => `Sc ${scene.scene_number}`) || [];
  const sceneScores = sceneRiskData?.map((scene) => scene.risk_score) || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8 p-4 md:p-6 bg-white dark:bg-gray-900 rounded-lg shadow-inner"
    >
      <div className="flex items-center justify-between border-b pb-4 mb-4 border-gray-200 dark:border-gray-700">
        <h3 className="text-2xl font-bold" style={{ color: "var(--text)" }}>
          📊 Real-Time Risk Monitor
        </h3>
        <span className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          Live
        </span>
      </div>

      {/* Hero Section: Gauge & Readiness */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="flex flex-col items-center"
        >
          <RiskGauge score={overall_risk_score} size="lg" showDetails={true} riskFactors={risk_assessment.risk_factors} />
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">Overall Risk Score</p>
            <AnimatedNumber value={Math.round(overall_risk_score)} />
            <p className={`font-semibold text-lg`} style={{ color: getRiskColor(overall_risk_score) }}>
              {risk_level} Risk
            </p>
          </div>
        </motion.div>
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg shadow-sm"
        >
          {riskDetail.readiness_scores ? (
            <ReadinessBars scores={riskDetail.readiness_scores} />
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400 py-4">
              Readiness scores not available.
            </div>
          )}
        </motion.div>
      </div>

      {/* Charts Section: Pie & Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg shadow-sm flex flex-col items-center"
        >
          <PieChart data={riskCategoryData} title="Risk Distribution by Category" size={250} />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg shadow-sm flex flex-col items-center"
        >
          <BarChart data={severityBarChartData} title="Issues by Severity" height={250} />
        </motion.div>
      </div>

      {/* Scene Risk Timeline */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1.0 }}
        className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg shadow-sm"
      >
        <TrendLine
          labels={sceneLabels}
          data={sceneScores}
          title="Scene Risk Timeline"
          color={getRiskColor(overall_risk_score)}
          height={200}
        />
      </motion.div>

      {/* Critical Issues Feed */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1.2 }}
        className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg shadow-sm"
      >
        <CriticalIssuesFeed issues={critical_issues} suggestions={suggestions || []} />
      </motion.div>

      {/* Agent Confidence */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 1.4 }}
        className="bg-gray-50 dark:bg-gray-800 p-6 rounded-lg shadow-sm"
      >
        {agent_flow && agent_flow.length > 0 ? (
          <AgentConfidenceBars agentFlow={agent_flow} />
        ) : (
          <div className="text-center text-gray-500 dark:text-gray-400 py-4">
            Agent flow data not available.
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
