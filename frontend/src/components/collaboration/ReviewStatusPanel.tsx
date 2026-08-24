"use client";

import type { ReviewStatus } from "@/lib/types";

interface ReviewStatusPanelProps {
  reviews: ReviewStatus[];
  currentUserId: string;
  onRequestReview: (reviewerId: string) => Promise<void>;
  onUpdateStatus: (reviewId: string, status: string, comments?: string) => Promise<void>;
}

const statusConfig: Record<string, { label: string; color: string; icon: string }> = {
  pending: { label: "Pending", color: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200", icon: "⏳" },
  approved: { label: "Approved", color: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200", icon: "✅" },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200", icon: "❌" },
  needs_changes: { label: "Needs Changes", color: "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200", icon: "🔄" },
};

export function ReviewStatusPanel({
  reviews,
  currentUserId,
  onRequestReview,
  onUpdateStatus,
}: ReviewStatusPanelProps) {
  const pendingReviews = reviews.filter((r) => r.status === "pending");
  const completedReviews = reviews.filter((r) => r.status !== "pending");

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Reviews ({reviews.length})
        </h3>
      </div>

      {reviews.length === 0 ? (
        <div className="py-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">No reviews requested yet.</p>
          <button
            onClick={() => onRequestReview(currentUserId)}
            className="mt-2 rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          >
            Request Review
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Pending reviews */}
          {pendingReviews.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">Pending</p>
              <div className="space-y-2">
                {pendingReviews.map((review) => {
                  const config = statusConfig[review.status];
                  const isReviewer = review.reviewer_id === currentUserId;
                  return (
                    <div
                      key={review.id}
                      className="rounded-lg bg-gray-50 p-3 dark:bg-gray-800/50"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span>{config?.icon}</span>
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            Reviewer: {review.reviewer_id.slice(0, 8)}
                          </span>
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${config?.color}`}>
                            {config?.label}
                          </span>
                        </div>
                      </div>
                      {isReviewer && (
                        <div className="mt-2 flex gap-2">
                          <button
                            onClick={() => onUpdateStatus(review.id, "approved")}
                            className="rounded-md bg-green-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-green-700"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => onUpdateStatus(review.id, "needs_changes")}
                            className="rounded-md bg-orange-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-orange-700"
                          >
                            Needs Changes
                          </button>
                          <button
                            onClick={() => onUpdateStatus(review.id, "rejected")}
                            className="rounded-md bg-red-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-red-700"
                          >
                            Reject
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Completed reviews */}
          {completedReviews.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-medium text-gray-500 dark:text-gray-400">Completed</p>
              <div className="space-y-2">
                {completedReviews.map((review) => {
                  const config = statusConfig[review.status];
                  return (
                    <div
                      key={review.id}
                      className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 dark:bg-gray-800/50"
                    >
                      <div className="flex items-center gap-2">
                        <span>{config?.icon}</span>
                        <span className="text-sm text-gray-700 dark:text-gray-300">
                          {review.reviewer_id.slice(0, 8)}
                        </span>
                        <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${config?.color}`}>
                          {config?.label}
                        </span>
                      </div>
                      {review.reviewed_at && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(review.reviewed_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
