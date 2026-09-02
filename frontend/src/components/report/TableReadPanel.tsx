"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface TTSScene {
  scene_number: number;
  title: string;
  characters: string[];
  audio_base64: string | null;
  audio_format: string;
  duration_seconds: number;
  generation_error: string | null;
}

interface TTSResponse {
  tts_id: string;
  report_id: string;
  success: boolean;
  scenes: TTSScene[];
  total_scenes: number;
  successful_scenes: number;
  voice_map: Record<string, string>;
  total_duration: number;
  processing_time: number;
  generated_at: string;
  error: string | null;
}

interface TableReadPanelProps {
  reportId: string;
}

export function TableReadPanel({ reportId }: TableReadPanelProps) {
  const [tts, setTts] = useState<TTSResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentScene, setCurrentScene] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [autoPlay, setAutoPlay] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const successfulScenes = tts?.scenes.filter((s) => s.audio_base64) || [];
  const totalDuration = successfulScenes.reduce((sum, s) => sum + s.duration_seconds, 0);

  const generateTTS = async () => {
    setLoading(true);
    setError(null);

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${API_URL}/api/tts/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report_id: reportId }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to generate table read");
      }

      const data: TTSResponse = await response.json();
      setTts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate table read");
    } finally {
      setLoading(false);
    }
  };

  // Create audio URL from base64
  const getAudioUrl = useCallback((scene: TTSScene): string | null => {
    if (!scene.audio_base64) return null;
    const binary = atob(scene.audio_base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: `audio/${scene.audio_format}` });
    return URL.createObjectURL(blob);
  }, []);

  // Play a specific scene
  const playScene = useCallback((sceneIndex: number) => {
    if (sceneIndex < 0 || sceneIndex >= successfulScenes.length) return;

    const scene = successfulScenes[sceneIndex];
    const audioUrl = getAudioUrl(scene);
    if (!audioUrl) return;

    // Stop current audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audio = new Audio(audioUrl);
    audio.volume = volume;
    audio.playbackRate = playbackRate;

    audio.onloadedmetadata = () => {
      setDuration(audio.duration);
      setCurrentTime(0);
    };

    audio.ontimeupdate = () => {
      setCurrentTime(audio.currentTime);
    };

    audio.onended = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      // Auto-play next scene
      if (autoPlay && sceneIndex < successfulScenes.length - 1) {
        setCurrentScene(sceneIndex + 1);
        playScene(sceneIndex + 1);
      }
    };

    audio.onerror = () => {
      setIsPlaying(false);
      setError(`Failed to play audio for Scene ${scene.scene_number}`);
    };

    audio.play().then(() => {
      setIsPlaying(true);
      setCurrentScene(sceneIndex);
    }).catch((err) => {
      console.error("Playback failed:", err);
    });

    audioRef.current = audio;
  }, [successfulScenes, volume, playbackRate, autoPlay, getAudioUrl]);

  // Toggle play/pause
  const togglePlayPause = useCallback(() => {
    if (!audioRef.current) {
      // Start playing from beginning
      if (successfulScenes.length > 0) {
        playScene(currentScene);
      }
      return;
    }

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  }, [isPlaying, currentScene, successfulScenes, playScene]);

  // Stop playback
  const stopPlayback = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    setIsPlaying(false);
    setCurrentTime(0);
  }, []);

  // Seek
  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  // Change volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);

  // Change playback rate
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.playbackRate = playbackRate;
    }
  }, [playbackRate]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🎙️ Table Read
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            AI-generated multi-voice read-through of your script
          </p>
        </div>
        {!tts && !loading && (
          <button
            onClick={generateTTS}
            className="rounded-lg bg-gradient-to-r from-green-600 to-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-lg hover:from-green-700 hover:to-emerald-700 transition-all"
          >
            🎤 Generate Table Read
          </button>
        )}
        {tts && (
          <button
            onClick={generateTTS}
            className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            🔄 Regenerate
          </button>
        )}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="py-12 text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-green-200 border-t-green-600" />
          </div>
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            Generating table read audio...
          </p>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            This may take 60-180 seconds depending on script length
          </p>
          <div className="mt-4 mx-auto max-w-xs">
            <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-gray-700">
              <div className="h-full w-1/3 animate-pulse rounded-full bg-gradient-to-r from-green-500 to-emerald-500" />
            </div>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-900/20">
          <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          <button
            onClick={generateTTS}
            className="mt-2 text-xs font-medium text-red-600 hover:text-red-800 dark:text-red-400"
          >
            Try again
          </button>
        </div>
      )}

      {/* Results */}
      {tts && !loading && (
        <div>
          {/* Stats Bar */}
          <div className="mb-4 flex items-center gap-4 text-sm">
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              🎵 <strong>{tts.successful_scenes}</strong> scenes
            </span>
            <span className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400">
              ⏱️ {formatTime(totalDuration)} total
            </span>
            <span className="text-gray-400 dark:text-gray-500">
              ⚡ {tts.processing_time.toFixed(1)}s
            </span>
          </div>

          {/* Voice Map */}
          {Object.keys(tts.voice_map).length > 0 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {Object.entries(tts.voice_map).map(([speaker, voice]) => (
                <span
                  key={speaker}
                  className="inline-flex items-center gap-1 rounded-full bg-purple-100 px-2.5 py-1 text-xs font-medium text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
                >
                  <span className="font-semibold">{speaker}</span>
                  <span className="text-purple-500">→</span>
                  <span>{voice}</span>
                </span>
              ))}
            </div>
          )}

          {/* Player Controls */}
          {successfulScenes.length > 0 && (
            <div className="mb-6 rounded-xl border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center gap-3">
                {/* Play/Pause button */}
                <button
                  onClick={togglePlayPause}
                  className="flex h-12 w-12 items-center justify-center rounded-full bg-green-600 text-white hover:bg-green-700 transition-colors"
                >
                  {isPlaying ? (
                    <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                    </svg>
                  ) : (
                    <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  )}
                </button>

                {/* Stop button */}
                <button
                  onClick={stopPlayback}
                  className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-300 text-gray-700 hover:bg-gray-400 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500 transition-colors"
                >
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M6 6h12v12H6z" />
                  </svg>
                </button>

                {/* Progress bar */}
                <div className="flex-1">
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                    <span>Scene {currentScene + 1}: {successfulScenes[currentScene]?.title}</span>
                    <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
                  </div>
                  <div
                    className="relative h-2 w-full cursor-pointer rounded-full bg-gray-200 dark:bg-gray-700"
                    onClick={(e) => {
                      const rect = e.currentTarget.getBoundingClientRect();
                      const pct = (e.clientX - rect.left) / rect.width;
                      seek(pct * duration);
                    }}
                  >
                    <div
                      className="absolute h-full rounded-full bg-green-500"
                      style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Secondary controls */}
              <div className="mt-3 flex items-center gap-4 text-sm">
                {/* Volume */}
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 dark:text-gray-400">🔊</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={volume}
                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                    className="w-20"
                  />
                </div>

                {/* Speed */}
                <div className="flex items-center gap-2">
                  <span className="text-gray-500 dark:text-gray-400">Speed:</span>
                  <select
                    value={playbackRate}
                    onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
                    className="rounded border border-gray-300 bg-white px-2 py-0.5 text-xs dark:border-gray-600 dark:bg-gray-800"
                  >
                    <option value="0.5">0.5x</option>
                    <option value="0.75">0.75x</option>
                    <option value="1">1x</option>
                    <option value="1.25">1.25x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                  </select>
                </div>

                {/* Auto-play */}
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoPlay}
                    onChange={(e) => setAutoPlay(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-gray-500 dark:text-gray-400">Auto-play next</span>
                </label>
              </div>
            </div>
          )}

          {/* Scene List */}
          {successfulScenes.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Scenes
              </h4>
              {successfulScenes.map((scene, idx) => (
                <SceneCard
                  key={scene.scene_number}
                  scene={scene}
                  isActive={currentScene === idx}
                  isPlaying={currentScene === idx && isPlaying}
                  onClick={() => {
                    setCurrentScene(idx);
                    playScene(idx);
                  }}
                  formatTime={formatTime}
                />
              ))}
            </div>
          )}

          {/* Empty State */}
          {successfulScenes.length === 0 && !loading && (
            <div className="py-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">
                No audio was generated. Try again or check the script content.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SceneCard({
  scene,
  isActive,
  isPlaying,
  onClick,
  formatTime,
}: {
  scene: TTSScene;
  isActive: boolean;
  isPlaying: boolean;
  onClick: () => void;
  formatTime: (s: number) => string;
}) {
  return (
    <div
      onClick={onClick}
      className={`flex items-center gap-4 rounded-lg border p-3 cursor-pointer transition-all ${
        isActive
          ? "border-green-300 bg-green-50 dark:border-green-700 dark:bg-green-900/20"
          : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
      }`}
    >
      {/* Play indicator */}
      <div className={`flex h-10 w-10 items-center justify-center rounded-full flex-shrink-0 ${
        isActive
          ? "bg-green-600 text-white"
          : "bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400"
      }`}>
        {isPlaying ? (
          <div className="flex items-center gap-0.5">
            <div className="w-0.5 h-3 bg-white animate-pulse" />
            <div className="w-0.5 h-4 bg-white animate-pulse" style={{ animationDelay: "0.1s" }} />
            <div className="w-0.5 h-2 bg-white animate-pulse" style={{ animationDelay: "0.2s" }} />
          </div>
        ) : (
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
          Scene {scene.scene_number}: {scene.title}
        </h4>
        <div className="mt-0.5 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>{formatTime(scene.duration_seconds)}</span>
          <span>·</span>
          <span>{scene.characters.length} speaker{scene.characters.length !== 1 ? "s" : ""}</span>
          <span>·</span>
          <span>{scene.characters.join(", ")}</span>
        </div>
      </div>

      {/* Duration */}
      <div className="text-right flex-shrink-0">
        <span className="text-sm font-mono text-gray-500 dark:text-gray-400">
          {formatTime(scene.duration_seconds)}
        </span>
      </div>
    </div>
  );
}
