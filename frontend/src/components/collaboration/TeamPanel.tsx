"use client";

import type { TeamMember, ProductionRole } from "@/lib/types";

interface TeamPanelProps {
  members: TeamMember[];
  currentUserId: string;
  onInvite: (role: ProductionRole) => Promise<void>;
  onRemove: (userId: string) => Promise<void>;
  onlineMembers?: { user_id: string; user_name: string }[];
}

const roleLabels: Record<ProductionRole, string> = {
  director: "Director",
  producer: "Producer",
  script_supervisor: "Script Supervisor",
  line_producer: "Line Producer",
  legal_affairs: "Legal Affairs",
  researcher: "Researcher",
};

const roleColors: Record<ProductionRole, string> = {
  director: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
  producer: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  script_supervisor: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
  legal_affairs: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
  researcher: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
  line_producer: "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200",
};

export function TeamPanel({
  members,
  currentUserId,
  onInvite,
  onRemove,
  onlineMembers = [],
}: TeamPanelProps) {
  const onlineIds = new Set(onlineMembers.map((m) => m.user_id));

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Team Members ({members.length})
        </h3>
      </div>

      {members.length === 0 ? (
        <p className="py-4 text-center text-sm text-gray-500 dark:text-gray-400">
          No team members yet.
        </p>
      ) : (
        <ul className="space-y-2">
          {members.map((member) => (
            <li
              key={member.id}
              className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"
            >
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-300 text-sm font-medium text-gray-700 dark:bg-gray-600 dark:text-gray-300">
                    {member.user_id.slice(0, 2).toUpperCase()}
                  </div>
                  {onlineIds.has(member.user_id) && (
                    <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white bg-green-500 dark:border-gray-800" />
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {member.user_id === currentUserId ? "You" : member.user_id.slice(0, 8)}
                  </p>
                  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${roleColors[member.role] ?? ""}`}>
                    {roleLabels[member.role] ?? member.role}
                  </span>
                </div>
              </div>
              {member.user_id !== currentUserId && (
                <button
                  onClick={() => onRemove(member.user_id)}
                  className="text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                >
                  Remove
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {/* Quick invite buttons */}
      <div className="mt-4">
        <p className="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">Quick Invite</p>
        <div className="flex flex-wrap gap-2">
          {(
            ["director", "producer", "script_supervisor", "legal_affairs", "researcher"] as ProductionRole[]
          ).map((role) => (
            <button
              key={role}
              onClick={() => onInvite(role)}
              className="rounded-full border border-gray-300 px-2.5 py-1 text-xs text-gray-700 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              + {roleLabels[role]}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
