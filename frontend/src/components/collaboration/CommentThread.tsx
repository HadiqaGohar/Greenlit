"use client";

import { useState } from "react";
import type { Comment as CommentType } from "@/lib/types";
import { CommentForm } from "./CommentForm";

interface CommentThreadProps {
  comments: CommentType[];
  currentUserId: string;
  currentUserName: string;
  currentUserRole?: string;
  onAddComment: (content: string, parentId?: string) => Promise<void>;
  onResolve: (commentId: string) => Promise<void>;
  onDelete: (commentId: string) => Promise<void>;
}

function CommentCard({
  comment,
  currentUserId,
  onReply,
  onResolve,
  onDelete,
  depth = 0,
}: {
  comment: CommentType;
  currentUserId: string;
  onReply: (parentId: string, content: string) => Promise<void>;
  onResolve: (commentId: string) => Promise<void>;
  onDelete: (commentId: string) => Promise<void>;
  depth?: number;
}) {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const isOwner = comment.user_id === currentUserId;

  const roleColors: Record<string, string> = {
    director: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
    producer: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    script_supervisor: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    legal_affairs: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200",
    researcher: "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200",
    line_producer: "bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200",
  };

  return (
    <div className={`${depth > 0 ? "ml-6 border-l-2 border-gray-200 pl-4 dark:border-gray-700" : ""}`}>
      <div className={`rounded-lg p-3 ${comment.resolved ? "opacity-60" : ""} bg-gray-50 dark:bg-gray-800/50`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {comment.user_name}
            </span>
            <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${roleColors[comment.user_role] ?? "bg-gray-100 text-gray-600"}`}>
              {comment.user_role.replace("_", " ")}
            </span>
            {comment.resolved && (
              <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800 dark:bg-green-900 dark:text-green-200">
                Resolved
              </span>
            )}
          </div>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {new Date(comment.created_at).toLocaleDateString()}
          </span>
        </div>
        <p className="mt-2 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
          {comment.content}
        </p>
        <div className="mt-2 flex gap-3">
          <button
            onClick={() => setShowReplyForm(!showReplyForm)}
            className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Reply
          </button>
          {!comment.resolved && (
            <button
              onClick={() => onResolve(comment.id)}
              className="text-xs text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
            >
              Resolve
            </button>
          )}
          {isOwner && (
            <button
              onClick={() => onDelete(comment.id)}
              className="text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
            >
              Delete
            </button>
          )}
        </div>
        {showReplyForm && (
          <div className="mt-3">
            <CommentForm
              onSubmit={(content) => onReply(comment.id, content)}
              placeholder="Write a reply..."
              parentId={comment.id}
              onCancel={() => setShowReplyForm(false)}
              compact
            />
          </div>
        )}
      </div>
      {/* Render replies */}
      {comment.replies?.map((reply) => (
        <CommentCard
          key={reply.id}
          comment={reply}
          currentUserId={currentUserId}
          onReply={onReply}
          onResolve={onResolve}
          onDelete={onDelete}
          depth={depth + 1}
        />
      ))}
    </div>
  );
}

export function CommentThread({
  comments,
  currentUserId,
  onAddComment,
  onResolve,
  onDelete,
}: CommentThreadProps) {
  // Organize into threaded structure
  const rootComments = comments.filter((c) => !c.parent_id);
  const childMap = new Map<string, CommentType[]>();
  comments.forEach((c) => {
    if (c.parent_id) {
      const children = childMap.get(c.parent_id) || [];
      children.push(c);
      childMap.set(c.parent_id, children);
    }
  });

  // Attach replies to parent comments
  const threaded = rootComments.map((c) => ({
    ...c,
    replies: childMap.get(c.id) || [],
  }));

  const handleReply = async (parentId: string, content: string) => {
    await onAddComment(content, parentId);
  };

  if (threaded.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-gray-500 dark:text-gray-400">
        No comments yet. Start the discussion!
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {threaded.map((comment) => (
        <CommentCard
          key={comment.id}
          comment={comment}
          currentUserId={currentUserId}
          onReply={handleReply}
          onResolve={onResolve}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
