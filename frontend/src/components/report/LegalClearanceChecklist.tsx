"use client";

import { useState } from "react";

interface ClearanceItem {
  id: string;
  type: "copyright" | "trademark" | "location" | "person" | "music" | "other";
  description: string;
  severity: "high" | "medium" | "low";
  status: "pending" | "in_progress" | "cleared" | "blocked";
  estimated_cost: string;
  action_required: string;
}

interface LegalClearanceChecklistProps {
  items: ClearanceItem[];
}

const typeIcons: Record<string, string> = {
  copyright: "©️",
  trademark: "™️",
  location: "📍",
  person: "👤",
  music: "🎵",
  other: "📋",
};

const severityColors: Record<string, string> = {
  high: "border-red-300 bg-red-50 dark:border-red-800 dark:bg-red-900/20",
  medium: "border-yellow-300 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20",
  low: "border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20",
};

const statusOptions: ClearanceItem["status"][] = [
  "pending",
  "in_progress",
  "cleared",
  "blocked",
];

export function LegalClearanceChecklist({ items }: LegalClearanceChecklistProps) {
  const [localItems, setLocalItems] = useState(items);
  const [filter, setFilter] = useState<"all" | ClearanceItem["status"]>("all");

  const updateStatus = (id: string, status: ClearanceItem["status"]) => {
    setLocalItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, status } : item))
    );
  };

  const filteredItems =
    filter === "all" ? localItems : localItems.filter((i) => i.status === filter);

  const clearedCount = localItems.filter((i) => i.status === "cleared").length;
  const totalCount = localItems.length;
  const progress = totalCount > 0 ? (clearedCount / totalCount) * 100 : 0;

  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Legal Clearance Checklist
        </h3>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          No legal issues found — script is clear!
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Legal Clearance Checklist
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Track clearance status for each legal issue
        </p>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="mb-1 flex justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>
            {clearedCount} of {totalCount} cleared
          </span>
          <span>{progress.toFixed(0)}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
          <div
            className="h-full rounded-full bg-green-500 transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="mb-4 flex flex-wrap gap-2">
        {(["all", "pending", "in_progress", "cleared", "blocked"] as const).map(
          (status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                filter === status
                  ? "bg-blue-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
              }`}
            >
              {status === "all"
                ? `All (${localItems.length})`
                : status === "in_progress"
                ? `In Progress (${localItems.filter((i) => i.status === "in_progress").length})`
                : `${status.charAt(0).toUpperCase() + status.slice(1)} (${
                    localItems.filter((i) => i.status === status).length
                  })`}
            </button>
          )
        )}
      </div>

      {/* Checklist Items */}
      <div className="space-y-3">
        {filteredItems.map((item) => (
          <div
            key={item.id}
            className={`rounded-lg border-2 p-4 ${severityColors[item.severity]}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <span className="text-xl">{typeIcons[item.type]}</span>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {item.description}
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        item.severity === "high"
                          ? "bg-red-200 text-red-800 dark:bg-red-800 dark:text-red-200"
                          : item.severity === "medium"
                          ? "bg-yellow-200 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200"
                          : "bg-blue-200 text-blue-800 dark:bg-blue-800 dark:text-blue-200"
                      }`}
                    >
                      {item.severity}
                    </span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Est: {item.estimated_cost}
                    </span>
                  </div>
                  <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                    <span className="font-medium">Action:</span> {item.action_required}
                  </p>
                </div>
              </div>

              {/* Status Dropdown */}
              <select
                value={item.status}
                onChange={(e) =>
                  updateStatus(item.id, e.target.value as ClearanceItem["status"])
                }
                className="rounded-lg border border-gray-300 bg-white px-2 py-1 text-xs dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
              >
                {statusOptions.map((status) => (
                  <option key={status} value={status}>
                    {status === "in_progress" ? "In Progress" : status.charAt(0).toUpperCase() + status.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
