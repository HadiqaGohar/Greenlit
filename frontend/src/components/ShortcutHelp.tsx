"use client";

interface ShortcutHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

const groups = [
  {
    category: "Navigation",
    items: [
      { keys: ["A"], desc: "Analyze script" },
      { keys: ["N"], desc: "New script" },
      { keys: ["D"], desc: "Go to Dashboard" },
      { keys: ["S"], desc: "Go to Settings" },
    ],
  },
  {
    category: "Actions",
    items: [
      { keys: ["E"], desc: "Export report" },
      { keys: ["R"], desc: "Refresh data" },
    ],
  },
  {
    category: "Report",
    items: [
      { keys: ["1"], desc: "Overview tab" },
      { keys: ["2"], desc: "Research tab" },
      { keys: ["3"], desc: "Legal tab" },
      { keys: ["4"], desc: "Continuity tab" },
    ],
  },
  {
    category: "General",
    items: [
      { keys: ["?"], desc: "Show shortcuts" },
      { keys: ["Esc"], desc: "Close modal" },
    ],
  },
];

export function ShortcutHelp({ isOpen, onClose }: ShortcutHelpProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="relative mx-4 w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-gray-900">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Keyboard Shortcuts
          </h2>
          <button onClick={onClose} className="rounded-md p-1 text-gray-400 hover:text-gray-600">
            X
          </button>
        </div>
        <div className="space-y-5">
          {groups.map((group) => (
            <div key={group.category}>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                {group.category}
              </h3>
              <div className="space-y-1.5">
                {group.items.map((item) => (
                  <div
                    key={item.desc}
                    className="flex items-center justify-between rounded-lg px-3 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">{item.desc}</span>
                    <div className="flex gap-1">
                      {item.keys.map((key) => (
                        <kbd
                          key={key}
                          className="inline-flex h-6 min-w-[24px] items-center justify-center rounded border border-gray-300 bg-gray-100 px-1.5 text-xs font-mono font-medium text-gray-800 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
                        >
                          {key}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className="mt-5 text-center text-xs text-gray-400">
          Press <kbd className="rounded border border-gray-300 px-1 dark:border-gray-600">?</kbd> to toggle this help
        </p>
      </div>
    </div>
  );
}
