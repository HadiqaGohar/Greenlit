"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Plus, Minus, Equal } from "lucide-react";

interface DiffLine {
  type: "added" | "removed" | "unchanged";
  content: string;
  lineNumber?: number;
}

interface DiffViewerProps {
  diff: string;
  addedLines: number;
  removedLines: number;
  similarity: number;
}

export function DiffViewer({
  diff,
  addedLines,
  removedLines,
  similarity,
}: DiffViewerProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Parse diff string into structured lines
  const parseDiff = (diffText: string): DiffLine[] => {
    const lines = diffText.split("\n");
    const result: DiffLine[] = [];
    let leftLine = 0;
    let rightLine = 0;

    for (const line of lines) {
      if (line.startsWith("@@")) {
        // Hunk header - extract line numbers
        const match = line.match(/@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/);
        if (match) {
          leftLine = parseInt(match[1]) - 1;
          rightLine = parseInt(match[2]) - 1;
        }
        continue;
      }

      if (line.startsWith("+++") || line.startsWith("---")) {
        continue;
      }

      if (line.startsWith("+")) {
        rightLine++;
        result.push({
          type: "added",
          content: line.substring(1),
          lineNumber: rightLine,
        });
      } else if (line.startsWith("-")) {
        leftLine++;
        result.push({
          type: "removed",
          content: line.substring(1),
          lineNumber: leftLine,
        });
      } else if (line.startsWith(" ")) {
        leftLine++;
        rightLine++;
        result.push({
          type: "unchanged",
          content: line.substring(1),
          lineNumber: leftLine,
        });
      }
    }

    return result;
  };

  const diffLines = parseDiff(diff);

  return (
    <div className="rounded-lg overflow-hidden" style={{ border: "1px solid var(--border)" }}>
      {/* Header */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer"
        style={{ backgroundColor: "var(--bg-secondary, var(--bg))" }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium" style={{ color: "var(--text)" }}>
            Changes
          </span>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1" style={{ color: "var(--verified)" }}>
              <Plus size={12} />
              {addedLines} added
            </span>
            <span className="flex items-center gap-1" style={{ color: "var(--flagged)" }}>
              <Minus size={12} />
              {removedLines} removed
            </span>
            <span className="flex items-center gap-1" style={{ color: "var(--text-muted)" }}>
              <Equal size={12} />
              {similarity}% similar
            </span>
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp size={16} style={{ color: "var(--text-muted)" }} />
        ) : (
          <ChevronDown size={16} style={{ color: "var(--text-muted)" }} />
        )}
      </div>

      {/* Diff Content */}
      {isExpanded && (
        <div
          className="max-h-96 overflow-y-auto"
          style={{ backgroundColor: "var(--bg)" }}
        >
          {diffLines.length === 0 ? (
            <div className="p-4 text-center text-sm" style={{ color: "var(--text-muted)" }}>
              No differences found
            </div>
          ) : (
            <table className="w-full text-sm font-mono">
              <tbody>
                {diffLines.map((line, i) => (
                  <tr
                    key={i}
                    style={{
                      backgroundColor:
                        line.type === "added"
                          ? "color-mix(in srgb, var(--verified) 10%, transparent)"
                          : line.type === "removed"
                          ? "color-mix(in srgb, var(--flagged) 10%, transparent)"
                          : "transparent",
                    }}
                  >
                    <td
                      className="w-8 px-2 py-0.5 text-right select-none"
                      style={{
                        color: "var(--text-muted)",
                        borderRight: "1px solid var(--border)",
                      }}
                    >
                      {line.lineNumber || ""}
                    </td>
                    <td
                      className="w-6 px-1 py-0.5 text-center select-none"
                      style={{
                        color:
                          line.type === "added"
                            ? "var(--verified)"
                            : line.type === "removed"
                            ? "var(--flagged)"
                            : "var(--text-muted)",
                      }}
                    >
                      {line.type === "added" ? "+" : line.type === "removed" ? "-" : " "}
                    </td>
                    <td className="px-2 py-0.5 whitespace-pre-wrap" style={{ color: "var(--text)" }}>
                      {line.content}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
