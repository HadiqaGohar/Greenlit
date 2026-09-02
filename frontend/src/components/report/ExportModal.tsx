"use client";

import { useState } from "react";
import { createExport, createShareLink } from "@/lib/api";

interface ExportModalProps {
  scriptId: string;
  userId: string;
  isOpen: boolean;
  onClose: () => void;
  report?: any;
}

type ExportFormat = "pdf" | "json" | "csv";
type Tab = "export" | "share";

const sectionOptions = [
  { id: "overview", label: "Overview", desc: "Risk score, agent performance" },
  { id: "claims", label: "Claims & Research", desc: "All claims with verdicts" },
  { id: "legal", label: "Legal Clearance", desc: "Copyright, trademark issues" },
  { id: "continuity", label: "Continuity", desc: "Timeline, character issues" },
];

const formatOptions: { id: ExportFormat; label: string; icon: string; desc: string }[] = [
  { id: "pdf", label: "PDF", icon: "📄", desc: "Professional report document" },
];

export function ExportModal({ scriptId, userId, isOpen, onClose, report }: ExportModalProps) {
  const [tab, setTab] = useState<Tab>("export");
  const [format, setFormat] = useState<ExportFormat>("pdf");
  const [selectedSections, setSelectedSections] = useState<string[]>(sectionOptions.map((s) => s.id));
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{ download_url?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [shareLink, setShareLink] = useState<string | null>(null);
  const [shareExpiry, setShareExpiry] = useState(72);
  const [isCreatingShare, setIsCreatingShare] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const toggleSection = (id: string) => {
    setSelectedSections((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]));
  };

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    setExportResult(null);
    try {
      const res = await createExport(
        { script_id: scriptId, format, sections: selectedSections, report_data: report },
        userId,
      );
      setExportResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setIsExporting(false);
    }
  };

  const handleCreateShare = async () => {
    setIsCreatingShare(true);
    try {
      const res = await createShareLink(scriptId, shareExpiry);
      setShareLink(`${window.location.origin}${res.share_url}`);
    } catch {
      setError("Failed to create share link");
    } finally {
      setIsCreatingShare(false);
    }
  };

  const handleCopy = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative mx-4 w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Export & Share
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        {/* Tabs */}
        <div className="mb-5 flex gap-1 rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
          <button
            onClick={() => setTab("export")}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === "export" ? "bg-white text-gray-900 shadow dark:bg-gray-700 dark:text-gray-100" : "text-gray-500"
            }`}
          >
            📥 Export File
          </button>
          <button
            onClick={() => setTab("share")}
            className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
              tab === "share" ? "bg-white text-gray-900 shadow dark:bg-gray-700 dark:text-gray-100" : "text-gray-500"
            }`}
          >
            🔗 Share Link
          </button>
        </div>

        {/* Export Tab */}
        {tab === "export" && (
          <div className="space-y-4">
            {/* Format selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Format
              </label>
              <div className="grid grid-cols-1 gap-2">
                {formatOptions.map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => setFormat(opt.id)}
                    className={`rounded-lg border p-3 text-center transition-colors ${
                      format === opt.id
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 hover:border-gray-300 dark:border-gray-700"
                    }`}
                  >
                    <span className="text-xl">{opt.icon}</span>
                    <p className="mt-1 text-sm font-medium text-gray-900 dark:text-gray-100">{opt.label}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{opt.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Sections */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sections
              </label>
              <div className="space-y-2">
                {sectionOptions.map((section) => (
                  <label
                    key={section.id}
                    className="flex items-center gap-3 rounded-lg border border-gray-200 px-3 py-2 dark:border-gray-700"
                  >
                    <input
                      type="checkbox"
                      checked={selectedSections.includes(section.id)}
                      onChange={() => toggleSection(section.id)}
                      className="rounded"
                    />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{section.label}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{section.desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            {/* Result */}
            {exportResult && (
              <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Export ready!
                </p>
                <button
                  onClick={() => {
                    const filename = exportResult.download_url?.split("/").pop();
                    if (filename) {
                      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
                      const link = document.createElement("a");
                      link.href = `${apiBase}/api/export/download/${filename}`;
                      link.download = filename;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }
                  }}
                  className="mt-2 rounded-md bg-green-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-green-700"
                >
                  Download {format.toUpperCase()}
                </button>
              </div>
            )}

            <button
              onClick={handleExport}
              disabled={isExporting || selectedSections.length === 0}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isExporting ? "Generating..." : `Export as ${format.toUpperCase()}`}
            </button>
          </div>
        )}

        {/* Share Tab */}
        {tab === "share" && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Link expires after
              </label>
              <select
                value={shareExpiry}
                onChange={(e) => setShareExpiry(Number(e.target.value))}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
              >
                <option value={24}>24 hours</option>
                <option value={72}>3 days</option>
                <option value={168}>7 days</option>
                <option value={720}>30 days</option>
              </select>
            </div>

            {shareLink && (
              <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
                <p className="text-sm font-medium text-green-800 dark:text-green-200 mb-2">
                  Share link created!
                </p>
                <div className="flex gap-2">
                  <input
                    readOnly
                    value={shareLink}
                    className="flex-1 rounded border border-gray-300 bg-white px-3 py-1.5 text-xs font-mono dark:border-gray-600 dark:bg-gray-800"
                  />
                  <button
                    onClick={handleCopy}
                    className="rounded bg-gray-200 px-3 py-1.5 text-xs font-medium hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600"
                  >
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
              </div>
            )}

            {error && <p className="text-sm text-red-600">{error}</p>}

            <button
              onClick={handleCreateShare}
              disabled={isCreatingShare}
              className="w-full rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {isCreatingShare ? "Creating..." : "Create Share Link"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
