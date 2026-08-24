"use client";

import { useEffect, useCallback, useState } from "react";

export interface Shortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  description: string;
  category: string;
  action: () => void;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: Omit<Shortcut, "action">[];
  onAction: (key: string) => void;
  enabled?: boolean;
}

export function useKeyboardShortcuts({
  shortcuts,
  onAction,
  enabled = true,
}: UseKeyboardShortcutsOptions) {
  const [showHelp, setShowHelp] = useState(false);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!enabled) return;

      // Ignore when typing in inputs
      const target = e.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.isContentEditable
      ) {
        // Allow Escape in inputs
        if (e.key !== "Escape") return;
      }

      // ? to toggle help
      if (e.key === "?" && !e.ctrlKey && !e.altKey && !e.shiftKey) {
        e.preventDefault();
        setShowHelp((prev) => !prev);
        return;
      }

      // Escape to close help
      if (e.key === "Escape" && showHelp) {
        setShowHelp(false);
        return;
      }

      // Check shortcuts
      for (const shortcut of shortcuts) {
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const ctrlMatch = !!shortcut.ctrl === (e.ctrlKey || e.metaKey);
        const shiftMatch = !!shortcut.shift === e.shiftKey;
        const altMatch = !!shortcut.alt === e.altKey;

        if (keyMatch && ctrlMatch && shiftMatch && altMatch) {
          // Don't override browser shortcuts
          if (e.ctrlKey || e.metaKey) {
            const browserShortcuts = ["c", "v", "x", "a", "z", "y", "s", "p", "f", "r"];
            if (browserShortcuts.includes(e.key.toLowerCase())) continue;
          }

          e.preventDefault();
          onAction(shortcut.key);
          return;
        }
      }
    },
    [shortcuts, onAction, enabled, showHelp],
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return { showHelp, setShowHelp };
}

// Default shortcut definitions
export const defaultShortcuts = [
  { key: "a", description: "Analyze script", category: "Navigation" },
  { key: "n", description: "New script", category: "Navigation" },
  { key: "d", description: "Go to Dashboard", category: "Navigation" },
  { key: "s", description: "Go to Settings", category: "Navigation" },
  { key: "/", description: "Focus search", category: "Navigation" },
  { key: "e", description: "Export report", category: "Actions" },
  { key: "r", description: "Refresh data", category: "Actions" },
  { key: "Escape", description: "Close modal / Go back", category: "General" },
  { key: "?", description: "Show keyboard shortcuts", category: "General" },
  { key: "1", description: "Switch to Overview tab", category: "Report" },
  { key: "2", description: "Switch to Research tab", category: "Report" },
  { key: "3", description: "Switch to Legal tab", category: "Report" },
  { key: "4", description: "Switch to Continuity tab", category: "Report" },
] as const;
