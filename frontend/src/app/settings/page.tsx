"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  getNotificationSettings,
  updateNotificationSettings,
  getWatchedFolders,
  addWatchFolder,
  removeWatchFolder,
  getAutomationStatus,
  ApiError,
} from "@/lib/api";
import type { NotificationSettings, WatchedFolder } from "@/lib/types";

// Mock user ID until auth is fully implemented
const MOCK_USER_ID = "default-user";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"notifications" | "automation">("notifications");
  const [settings, setSettings] = useState<NotificationSettings | null>(null);
  const [folders, setFolders] = useState<WatchedFolder[]>([]);
  const [automationStatus, setAutomationStatus] = useState<{ file_watching: boolean }>({ file_watching: false });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  // Folder form state
  const [newFolderPath, setNewFolderPath] = useState("");
  const [newFolderAutoAnalyze, setNewFolderAutoAnalyze] = useState(true);
  const [isAddingFolder, setIsAddingFolder] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [settingsData, foldersData, statusData] = await Promise.allSettled([
        getNotificationSettings(MOCK_USER_ID),
        getWatchedFolders(),
        getAutomationStatus(),
      ]);

      if (settingsData.status === "fulfilled") setSettings(settingsData.value);
      if (foldersData.status === "fulfilled") setFolders(foldersData.value.folders ?? []);
      if (statusData.status === "fulfilled") setAutomationStatus(statusData.value);
    } catch (err) {
      // Use defaults
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSaveSettings() {
    if (!settings) return;
    setIsSaving(true);
    setSaveMessage(null);
    try {
      await updateNotificationSettings(MOCK_USER_ID, settings);
      setSaveMessage("Settings saved successfully!");
      setTimeout(() => setSaveMessage(null), 3000);
    } catch {
      setSaveMessage("Failed to save settings.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAddFolder() {
    if (!newFolderPath.trim()) return;
    setIsAddingFolder(true);
    try {
      const result = await addWatchFolder({
        folder_path: newFolderPath.trim(),
        folder_type: "local",
        auto_analyze: newFolderAutoAnalyze,
      });
      setFolders((prev) => [
        ...prev,
        {
          watch_id: result.watch_id,
          folder_path: newFolderPath.trim(),
          folder_type: "local",
          auto_analyze: newFolderAutoAnalyze,
        },
      ]);
      setNewFolderPath("");
      setNewFolderAutoAnalyze(true);
    } catch {
      // Handle error
    } finally {
      setIsAddingFolder(false);
    }
  }

  async function handleRemoveFolder(watchId: string) {
    try {
      await removeWatchFolder(watchId);
      setFolders((prev) => prev.filter((f) => f.watch_id !== watchId));
    } catch {
      // Handle error
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="text-center text-gray-500">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          href="/dashboard"
          className="text-sm text-amber hover:text-amber-light transition-colors"
        >
          ← Back to dashboard
        </Link>
        <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-gray-100">Settings</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Configure notifications, file monitoring, and automation preferences.
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
        <button
          onClick={() => setActiveTab("notifications")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "notifications"
              ? "bg-white text-gray-900 shadow dark:bg-gray-700 dark:text-gray-100"
              : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          }`}
        >
          🔔 Notifications
        </button>
        <button
          onClick={() => setActiveTab("automation")}
          className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === "automation"
              ? "bg-white text-gray-900 shadow dark:bg-gray-700 dark:text-gray-100"
              : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
          }`}
        >
          ⚙️ File Monitoring
        </button>
      </div>

      {/* Notification Settings */}
      {activeTab === "notifications" && settings && (
        <div className="space-y-6">
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
              Notification Channels
            </h2>

            {/* Email notifications */}
            <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Email Notifications
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Receive alerts via email
                </p>
              </div>
              <Toggle
                checked={settings.email_enabled}
                onChange={(v) => setSettings({ ...settings, email_enabled: v })}
              />
            </div>

            {/* Slack notifications */}
            <div className="py-3 border-b border-gray-100 dark:border-gray-800">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Slack Notifications
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Send alerts to Slack channel
                  </p>
                </div>
                <Toggle
                  checked={settings.slack_enabled}
                  onChange={(v) => setSettings({ ...settings, slack_enabled: v })}
                />
              </div>
              {settings.slack_enabled && (
                <div className="mt-3">
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Slack Webhook URL
                  </label>
                  <input
                    type="url"
                    value={settings.slack_webhook}
                    onChange={(e) => setSettings({ ...settings, slack_webhook: e.target.value })}
                    placeholder="https://hooks.slack.com/services/..."
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                  />
                </div>
              )}
            </div>

            {/* Comment notifications */}
            <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-gray-800">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Comment Alerts
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Notify when someone comments on your scripts
                </p>
              </div>
              <Toggle
                checked={settings.notify_on_comments}
                onChange={(v) => setSettings({ ...settings, notify_on_comments: v })}
              />
            </div>

            {/* Completion notifications */}
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  Analysis Complete
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Notify when script analysis finishes
                </p>
              </div>
              <Toggle
                checked={settings.notify_on_completion}
                onChange={(v) => setSettings({ ...settings, notify_on_completion: v })}
              />
            </div>
          </div>

          {/* Alert Thresholds */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
              Alert Thresholds
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  High Risk Threshold: {settings.high_risk_threshold}
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={settings.high_risk_threshold}
                  onChange={(e) =>
                    setSettings({ ...settings, high_risk_threshold: Number(e.target.value) })
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                  <span>Low (0)</span>
                  <span>Critical (100)</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Digest Frequency
                </label>
                <select
                  value={settings.digest_frequency}
                  onChange={(e) =>
                    setSettings({ ...settings, digest_frequency: e.target.value })
                  }
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
                >
                  <option value="realtime">Real-time</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="never">Never</option>
                </select>
              </div>
            </div>
          </div>

          {/* Save button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSaveSettings}
              disabled={isSaving}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isSaving ? "Saving..." : "Save Settings"}
            </button>
            {saveMessage && (
              <span
                className={`text-sm ${
                  saveMessage.includes("success")
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {saveMessage}
              </span>
            )}
          </div>
        </div>
      )}

      {/* File Monitoring Settings */}
      {activeTab === "automation" && (
        <div className="space-y-6">
          {/* Status */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
            <div className="flex items-center gap-3">
              <span
                className={`h-3 w-3 rounded-full ${
                  automationStatus.file_watching ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  File Watcher
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {automationStatus.file_watching
                    ? "Monitoring folders for new scripts"
                    : "File watcher is not running"}
                </p>
              </div>
            </div>
          </div>

          {/* Add folder form */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
              Add Watched Folder
            </h2>
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="text"
                value={newFolderPath}
                onChange={(e) => setNewFolderPath(e.target.value)}
                placeholder="/path/to/scripts/folder"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              />
              <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                <input
                  type="checkbox"
                  checked={newFolderAutoAnalyze}
                  onChange={(e) => setNewFolderAutoAnalyze(e.target.checked)}
                  className="rounded"
                />
                Auto-analyze
              </label>
              <button
                onClick={handleAddFolder}
                disabled={!newFolderPath.trim() || isAddingFolder}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {isAddingFolder ? "Adding..." : "Add Folder"}
              </button>
            </div>
          </div>

          {/* Watched folders list */}
          <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-900">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">
              Watched Folders ({folders.length})
            </h2>
            {folders.length === 0 ? (
              <p className="py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                No folders being monitored. Add a folder above to get started.
              </p>
            ) : (
              <ul className="space-y-3">
                {folders.map((folder) => (
                  <li
                    key={folder.watch_id}
                    className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3 dark:bg-gray-800/50"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">📁</span>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 font-mono">
                          {folder.folder_path}
                        </p>
                        <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                          <span>Type: {folder.folder_type}</span>
                          <span>
                            Auto-analyze: {folder.auto_analyze ? "Yes" : "No"}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRemoveFolder(folder.watch_id)}
                      className="rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? "bg-blue-600" : "bg-gray-300 dark:bg-gray-600"
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}
