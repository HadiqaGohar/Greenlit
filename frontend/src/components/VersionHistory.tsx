"use client";

import { useState, useEffect } from "react";
import { Clock, RotateCcw, GitCompare, User, FileText } from "lucide-react";
import { DiffViewer } from "./DiffViewer";

interface Version {
  id: string;
  script_id: string;
  version_number: number;
  created_by: string;
  message: string;
  created_at: string;
  word_count: number;
  line_count: number;
}

interface DiffResult {
  diff: string;
  added_lines: number;
  removed_lines: number;
  similarity_percentage: number;
  version_1: { id: string; number: number };
  version_2: { id: string; number: number };
}

interface VersionHistoryProps {
  scriptId: string;
  onRollback?: (versionId: string) => void;
}

export function VersionHistory({ scriptId, onRollback }: VersionHistoryProps) {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersions, setSelectedVersions] = useState<string[]>([]);
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [comparing, setComparing] = useState(false);

  useEffect(() => {
    loadVersions();
  }, [scriptId]);

  const loadVersions = async () => {
    setLoading(true);
    try {
      // Mock data for demo
      const mockVersions: Version[] = [
        {
          id: "v1",
          script_id: scriptId,
          version_number: 3,
          created_by: "user",
          message: "Updated dialogue in Scene 5",
          created_at: new Date(Date.now() - 3600000).toISOString(),
          word_count: 2450,
          line_count: 142,
        },
        {
          id: "v2",
          script_id: scriptId,
          version_number: 2,
          created_by: "collaborator",
          message: "Fixed historical references",
          created_at: new Date(Date.now() - 86400000).toISOString(),
          word_count: 2380,
          line_count: 138,
        },
        {
          id: "v3",
          script_id: scriptId,
          version_number: 1,
          created_by: "user",
          message: "Initial script upload",
          created_at: new Date(Date.now() - 172800000).toISOString(),
          word_count: 2200,
          line_count: 128,
        },
      ];
      setVersions(mockVersions);
    } catch (error) {
      console.error("Failed to load versions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectVersion = (versionId: string) => {
    setSelectedVersions((prev) => {
      if (prev.includes(versionId)) {
        return prev.filter((id) => id !== versionId);
      }
      if (prev.length >= 2) {
        return [prev[1], versionId];
      }
      return [...prev, versionId];
    });
  };

  const handleCompare = async () => {
    if (selectedVersions.length !== 2) return;

    setComparing(true);
    try {
      // Mock diff for demo
      const mockDiff: DiffResult = {
        diff: `--- Version 2\n+++ Version 3\n@@ -10,8 +10,12 @@\n INT. OFFICE - DAY\n \n-JOHN enters the room quietly.\n+JOHN bursts into the room, visibly upset.\n \n-MARY looks up from her desk.\n+MARY jumps, startled by the sudden entrance.\n+\n+JOHN\n+  We need to talk. Now.\n+\n MARY\n-  Good morning, John.\n+  What's wrong? You look terrible.`,
        added_lines: 8,
        removed_lines: 4,
        similarity_percentage: 87.5,
        version_1: { id: selectedVersions[0], number: 2 },
        version_2: { id: selectedVersions[1], number: 3 },
      };
      setDiffResult(mockDiff);
    } catch (error) {
      console.error("Failed to compare versions:", error);
    } finally {
      setComparing(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-20 rounded-lg animate-pulse"
            style={{ backgroundColor: "var(--border)" }}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>
          Version History ({versions.length} versions)
        </h3>
        {selectedVersions.length === 2 && (
          <button
            onClick={handleCompare}
            disabled={comparing}
            className="flex items-center gap-2 px-3 py-1.5 rounded text-xs font-medium"
            style={{
              backgroundColor: "var(--accent)",
              color: "var(--accent-contrast)",
            }}
          >
            <GitCompare size={12} />
            {comparing ? "Comparing..." : "Compare"}
          </button>
        )}
      </div>

      {/* Version List */}
      <div className="space-y-2">
        {versions.map((version) => (
          <div
            key={version.id}
            className="p-3 rounded-lg cursor-pointer transition-colors"
            style={{
              border: `1px solid ${
                selectedVersions.includes(version.id)
                  ? "var(--accent)"
                  : "var(--border)"
              }`,
              backgroundColor: selectedVersions.includes(version.id)
                ? "color-mix(in srgb, var(--accent) 5%, var(--bg))"
                : "var(--bg)",
            }}
            onClick={() => handleSelectVersion(version.id)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{
                    backgroundColor: "var(--border)",
                    color: "var(--text)",
                  }}
                >
                  v{version.version_number}
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: "var(--text)" }}>
                    {version.message}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: "var(--text-muted)" }}>
                    <span className="flex items-center gap-1">
                      <User size={10} />
                      {version.created_by}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={10} />
                      {formatDate(version.created_at)}
                    </span>
                    <span className="flex items-center gap-1">
                      <FileText size={10} />
                      {version.word_count} words
                    </span>
                  </div>
                </div>
              </div>

              {version.version_number > 1 && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRollback?.(version.id);
                  }}
                  className="p-1.5 rounded hover:opacity-80 transition-colors"
                  style={{ color: "var(--text-muted)" }}
                  title="Rollback to this version"
                >
                  <RotateCcw size={14} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Diff Viewer */}
      {diffResult && (
        <DiffViewer
          diff={diffResult.diff}
          addedLines={diffResult.added_lines}
          removedLines={diffResult.removed_lines}
          similarity={diffResult.similarity_percentage}
        />
      )}
    </div>
  );
}
