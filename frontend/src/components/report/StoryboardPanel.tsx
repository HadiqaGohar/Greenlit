"use client";

import { useState } from "react";

interface StoryboardFrame {
  scene_number: number;
  title: string;
  description: string;
  mood: string;
  camera_angle: string;
  visual_prompt: string;
  image_base64: string | null;
  image_mime_type: string;
  generation_error: string | null;
}

interface StoryboardResponse {
  storyboard_id: string;
  report_id: string;
  success: boolean;
  frames: StoryboardFrame[];
  total_frames: number;
  successful_frames: number;
  failed_frames: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

interface StoryboardPanelProps {
  reportId: string;
}

export function StoryboardPanel({ reportId }: StoryboardPanelProps) {
  const [storyboard, setStoryboard] = useState<StoryboardResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFrame, setSelectedFrame] = useState<StoryboardFrame | null>(null);

  const generateStoryboard = async () => {
    setLoading(true);
    setError(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/api/storyboard/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to generate storyboard");
      }

      const data: StoryboardResponse = await response.json();
      setStoryboard(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate storyboard");
    } finally {
      setLoading(false);
    }
  };

  const successfulFrames = storyboard?.frames.filter((f) => f.image_base64) || [];
  const failedFrames = storyboard?.frames.filter((f) => !f.image_base64) || [];

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🎬 AI Storyboard
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Cinematic visuals generated for each scene using Imagen 4
          </p>
        </div>
        {!storyboard && !loading && (
          <button
            onClick={generateStoryboard}
            className="rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:from-purple-700 hover:to-blue-700 transition-all"
          >
            ✨ Generate Storyboard
          </button>
        )}
        {storyboard && (
          <button
            onClick={generateStoryboard}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            🔄 Regenerate
          </button>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="py-12 text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-purple-100 dark:bg-purple-900/30">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-purple-200 border-t-purple-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            Generating storyboard frames...
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            This may take 30-120 seconds depending on scene count
          </p>
          <div className="mt-4 mx-auto max-w-xs">
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-purple-500 to-blue-500" />
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          <button
            onClick={generateStoryboard}
            className="mt-2 text-xs font-medium text-red-600 hover:text-red-800 dark:text-red-400"
          >
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      {storyboard && !loading && (
        <div>
          {/* Stats Bar */}
          <div className="mb-6 flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              🖼️ <strong>{storyboard.successful_frames}</strong> frames generated
            </span>
            {storyboard.failed_frames > 0 && (
              <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                ⚠️ <strong>{storyboard.failed_frames}</strong> failed
              </span>
            )}
            <span className="text-gray-400 dark:text-gray-500">
              ⏱️ {storyboard.processing_time.toFixed(1)}s
            </span>
          </div>

          {/* Empty State */}
          {successfulFrames.length === 0 && !loading && (
            <div className="py-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                No storyboard frames were generated. Try again or check the script content.
              </p>
            </div>
          )}

          {/* Storyboard Grid */}
          {successfulFrames.length > 0 && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {successfulFrames.map((frame) => (
                <StoryboardCard
                  key={frame.scene_number}
                  frame={frame}
                  onClick={() => setSelectedFrame(frame)}
                />
              ))}
            </div>
          )}

          {/* Failed Frames */}
          {failedFrames.length > 0 && (
            <div className="mt-6">
              <h4 className="mb-3 text-sm font-medium text-gray-500 dark:text-gray-400">
                Failed Frames
              </h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {failedFrames.map((frame) => (
                  <FailedFrameCard key={frame.scene_number} frame={frame} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Lightbox Modal */}
      {selectedFrame && (
        <LightboxModal
          frame={selectedFrame}
          onClose={() => setSelectedFrame(null)}
        />
      )}
    </div>
  );
}

function StoryboardCard({
  frame,
  onClick,
}: {
  frame: StoryboardFrame;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className="group cursor-pointer overflow-hidden rounded-xl border border-gray-200 bg-gray-50 transition-all hover:shadow-lg hover:border-purple-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-purple-600"
    >
      {/* Image */}
      <div className="relative aspect-video overflow-hidden bg-gray-900">
        {frame.image_base64 && (
          <img
            src={`data:${frame.image_mime_type};base64,${frame.image_base64}`}
            alt={`Scene ${frame.scene_number}: ${frame.title}`}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        )}
        {/* Scene Number Badge */}
        <div className="absolute left-2 top-2 rounded-md bg-black/70 px-2 py-1 text-xs font-bold text-white">
          Scene {frame.scene_number}
        </div>
        {/* Mood Badge */}
        <div className="absolute right-2 top-2 rounded-md bg-purple-600/90 px-2 py-1 text-xs font-medium text-white capitalize">
          {frame.mood}
        </div>
        {/* Hover Overlay */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors group-hover:bg-black/30">
          <span className="rounded-lg bg-white/90 px-3 py-1.5 text-sm font-medium text-gray-900 opacity-0 transition-opacity group-hover:opacity-100">
            🔍 View Full
          </span>
        </div>
      </div>

      {/* Info */}
      <div className="p-3">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
          {frame.title}
        </h4>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 line-clamp-2">
          {frame.description}
        </p>
        <div className="mt-2 flex items-center gap-2 text-xs text-gray-400 dark:text-gray-500">
          <span>📷 {frame.camera_angle}</span>
        </div>
      </div>
    </div>
  );
}

function FailedFrameCard({ frame }: { frame: StoryboardFrame }) {
  return (
    <div className="overflow-hidden rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20">
      <div className="flex items-start gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/50">
          <span className="text-sm">⚠️</span>
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-medium text-amber-800 dark:text-amber-200">
            Scene {frame.scene_number}: {frame.title}
          </h4>
          <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
            {frame.generation_error}
          </p>
        </div>
      </div>
    </div>
  );
}

function LightboxModal({
  frame,
  onClose,
}: {
  frame: StoryboardFrame;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Content */}
      <div className="relative max-h-[90vh] max-w-5xl w-full overflow-hidden rounded-2xl bg-gray-900 shadow-2xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-3 top-3 z-10 rounded-full bg-black/50 p-2 text-white hover:bg-black/70 transition-colors"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Image */}
        {frame.image_base64 && (
          <div className="aspect-video w-full bg-black">
            <img
              src={`data:${frame.image_mime_type};base64,${frame.image_base64}`}
              alt={`Scene ${frame.scene_number}: ${frame.title}`}
              className="h-full w-full object-contain"
            />
          </div>
        )}

        {/* Info Panel */}
        <div className="p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold text-white">
                Scene {frame.scene_number}: {frame.title}
              </h3>
              <p className="mt-1 text-sm text-gray-400">{frame.description}</p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="rounded-full bg-purple-600/30 px-2.5 py-1 text-purple-300 capitalize">
                {frame.mood}
              </span>
              <span className="rounded-full bg-blue-600/30 px-2.5 py-1 text-blue-300">
                {frame.camera_angle}
              </span>
            </div>
          </div>

          {/* Visual Prompt (collapsible) */}
          <details className="mt-4 group">
            <summary className="cursor-pointer text-xs font-medium text-gray-500 hover:text-gray-300 transition-colors">
              📝 Visual Prompt Used
            </summary>
            <p className="mt-2 rounded-lg bg-gray-800 p-3 text-xs text-gray-400 leading-relaxed">
              {frame.visual_prompt}
            </p>
          </details>
        </div>
      </div>
    </div>
  );
}
