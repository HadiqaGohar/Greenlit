"use client";

import { useState, useEffect, useCallback } from "react";
import type {
  Comment as CommentType,
  TeamMember,
  ReviewStatus,
  ActivityItem,
  ProductionRole,
  WSMessage,
} from "@/lib/types";
import { useWebSocket } from "@/hooks/useWebSocket";
import * as api from "@/lib/api";
import { CommentThread } from "./CommentThread";
import { CommentForm } from "./CommentForm";
import { TeamPanel } from "./TeamPanel";
import { ReviewStatusPanel } from "./ReviewStatusPanel";
import { ActivityFeed } from "./ActivityFeed";
import { NotificationCenter } from "./NotificationCenter";
import type { Notification } from "@/lib/types";

type Tab = "comments" | "team" | "reviews" | "activity";

interface CollaborationPanelProps {
  scriptId: string;
  userId: string;
  userName: string;
  userRole?: ProductionRole;
  claimId?: string;
  sceneId?: string;
}

export function CollaborationPanel({
  scriptId,
  userId,
  userName,
  userRole = "researcher",
  claimId,
  sceneId,
}: CollaborationPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>("comments");
  const [comments, setComments] = useState<CommentType[]>([]);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [reviews, setReviews] = useState<ReviewStatus[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [onlineMembers, setOnlineMembers] = useState<{ user_id: string; user_name: string }[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // WebSocket for real-time sync
  const handleWSMessage = useCallback(
    (message: WSMessage) => {
      switch (message.type) {
        case "comment_added":
          setComments((prev) => [...prev, message.comment as CommentType]);
          break;
        case "comment_updated":
          setComments((prev) =>
            prev.map((c) => (c.id === (message.comment as CommentType).id ? (message.comment as CommentType) : c)),
          );
          break;
        case "comment_deleted":
          setComments((prev) => prev.filter((c) => c.id !== message.comment_id));
          break;
        case "issue_resolved":
          setComments((prev) =>
            prev.map((c) => (c.id === message.comment_id ? { ...c, resolved: true } : c)),
          );
          break;
        case "review_status_changed":
        case "review_requested":
          loadReviews();
          break;
        case "team_member_added":
        case "team_member_removed":
          loadTeam();
          break;
        case "user_joined":
        case "user_left":
          setOnlineMembers(message.members || []);
          break;
        case "script_status_updated":
          // Could trigger parent refresh
          break;
      }
    },
    [scriptId],
  );

  const { isConnected } = useWebSocket({
    scriptId,
    userId,
    userName,
    onMessage: handleWSMessage,
  });

  // Load initial data
  const loadComments = useCallback(async () => {
    try {
      const data = await api.getComments(scriptId, claimId, sceneId);
      setComments(data);
    } catch {}
  }, [scriptId, claimId, sceneId]);

  const loadTeam = useCallback(async () => {
    try {
      const data = await api.getTeamMembers(scriptId);
      setTeamMembers(data);
    } catch {}
  }, [scriptId]);

  const loadReviews = useCallback(async () => {
    try {
      const data = await api.getReviews(scriptId);
      setReviews(data);
    } catch {}
  }, [scriptId]);

  const loadActivity = useCallback(async () => {
    try {
      const data = await api.getActivityFeed(scriptId);
      setActivities(data.activities);
    } catch {}
  }, [scriptId]);

  const loadOnline = useCallback(async () => {
    try {
      const data = await api.getOnlineMembers(scriptId);
      setOnlineMembers(data.members);
    } catch {}
  }, [scriptId]);

  const loadNotifications = useCallback(async () => {
    try {
      const data = await api.getNotifications(userId);
      setNotifications(data.notifications);
    } catch {}
  }, [userId]);

  useEffect(() => {
    loadComments();
    loadTeam();
    loadReviews();
    loadActivity();
    loadOnline();
    loadNotifications();
  }, [loadComments, loadTeam, loadReviews, loadActivity, loadOnline, loadNotifications]);

  // Comment handlers
  const handleAddComment = async (content: string, parentId?: string) => {
    const comment = await api.createComment(
      scriptId,
      content,
      userId,
      userName,
      userRole,
      claimId,
      sceneId,
      parentId,
    );
    setComments((prev) => [...prev, comment]);
  };

  const handleResolve = async (commentId: string) => {
    await api.resolveComment(commentId, userId, userName);
    setComments((prev) => prev.map((c) => (c.id === commentId ? { ...c, resolved: true } : c)));
  };

  const handleDelete = async (commentId: string) => {
    await api.deleteComment(commentId, userId);
    setComments((prev) => prev.filter((c) => c.id !== commentId));
  };

  // Team handlers
  const handleInvite = async (role: ProductionRole) => {
    await api.inviteTeamMember(scriptId, userId, role);
    loadTeam();
  };

  const handleRemoveMember = async (targetUserId: string) => {
    await api.removeTeamMember(scriptId, targetUserId, userId);
    loadTeam();
  };

  // Review handlers
  const handleRequestReview = async (reviewerId: string) => {
    await api.createReviewRequest(scriptId, reviewerId, userId);
    loadReviews();
  };

  const handleUpdateReview = async (reviewId: string, status: string, comments?: string) => {
    await api.updateReviewStatus(reviewId, status, userId, userName, comments);
    loadReviews();
  };

  const tabs: { key: Tab; label: string; count?: number }[] = [
    { key: "comments", label: "Comments", count: comments.length },
    { key: "team", label: "Team", count: teamMembers.length },
    { key: "reviews", label: "Reviews", count: reviews.filter((r) => r.status === "pending").length },
    { key: "activity", label: "Activity" },
  ];

  return (
    <div className="flex h-full flex-col rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Collaboration</h2>
          <span
            className={`h-2 w-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
            title={isConnected ? "Connected" : "Disconnected"}
          />
        </div>
        <div className="flex items-center gap-3">
          {onlineMembers.length > 0 && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {onlineMembers.length} online
            </span>
          )}
          <NotificationCenter
            notifications={notifications}
            onMarkRead={async (id) => {
              await api.markNotificationRead(id);
              setNotifications((prev) =>
                prev.map((n) => (n.id === id ? { ...n, read: true } : n)),
              );
            }}
            onMarkAllRead={async () => {
              await api.markAllNotificationsRead(userId);
              setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
            }}
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 px-3 py-2.5 text-xs font-medium transition-colors ${
              activeTab === tab.key
                ? "border-b-2 border-blue-600 text-blue-600 dark:text-blue-400"
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className="ml-1 rounded-full bg-gray-200 px-1.5 py-0.5 text-[10px] dark:bg-gray-700">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "comments" && (
          <div>
            <CommentForm onSubmit={handleAddComment} placeholder="Add a comment to this script..." />
            <div className="mt-4">
              <CommentThread
                comments={comments}
                currentUserId={userId}
                onAddComment={handleAddComment}
                onResolve={handleResolve}
                onDelete={handleDelete}
              />
            </div>
          </div>
        )}

        {activeTab === "team" && (
          <TeamPanel
            members={teamMembers}
            currentUserId={userId}
            onInvite={handleInvite}
            onRemove={handleRemoveMember}
            onlineMembers={onlineMembers}
          />
        )}

        {activeTab === "reviews" && (
          <ReviewStatusPanel
            reviews={reviews}
            currentUserId={userId}
            onRequestReview={handleRequestReview}
            onUpdateStatus={handleUpdateReview}
          />
        )}

        {activeTab === "activity" && <ActivityFeed activities={activities} />}
      </div>
    </div>
  );
}
