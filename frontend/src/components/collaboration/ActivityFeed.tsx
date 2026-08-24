"use client";

import type { ActivityItem } from "@/lib/types";

interface ActivityFeedProps {
  activities: ActivityItem[];
  maxItems?: number;
}

function activityIcon(type: string) {
  switch (type) {
    case "comment":
      return "💬";
    case "review":
      return "📋";
    case "status_change":
      return "🔄";
    case "member_added":
      return "👤";
    default:
      return "📌";
  }
}

function activityText(activity: ActivityItem) {
  switch (activity.type) {
    case "comment":
      return (
        <>
          <strong>{activity.user_name ?? "Someone"}</strong> commented:{" "}
          <span className="text-gray-600 dark:text-gray-400">&ldquo;{activity.content}&rdquo;</span>
        </>
      );
    case "review":
      return (
        <>
          Review <strong>{activity.status}</strong>{" "}
          {activity.user_name ? `by ${activity.user_name}` : ""}
        </>
      );
    case "status_change":
      return <>Script status changed to <strong>{activity.status}</strong></>;
    case "member_added":
      return <><strong>{activity.user_name}</strong> joined the team</>;
    default:
      return <>Activity: {activity.type}</>;
  }
}

export function ActivityFeed({ activities, maxItems = 15 }: ActivityFeedProps) {
  const items = activities.slice(0, maxItems);

  if (items.length === 0) {
    return (
      <p className="py-4 text-center text-sm text-gray-500 dark:text-gray-400">
        No recent activity.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {items.map((activity, i) => (
        <li key={i} className="flex gap-3">
          <span className="mt-0.5 text-lg">{activityIcon(activity.type)}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {activityText(activity)}
            </p>
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
              {new Date(activity.timestamp).toLocaleString()}
            </p>
          </div>
          {activity.resolved !== undefined && (
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                activity.resolved
                  ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                  : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
              }`}
            >
              {activity.resolved ? "Resolved" : "Open"}
            </span>
          )}
        </li>
      ))}
    </ul>
  );
}
