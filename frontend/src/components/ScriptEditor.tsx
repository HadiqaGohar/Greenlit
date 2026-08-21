"use client";

import { ChangeEvent, useRef } from "react";

interface ScriptEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export function ScriptEditor({ value, onChange, disabled }: ScriptEditorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const text = await file.text();
    onChange(text);
    event.target.value = "";
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <label
          htmlFor="script-input"
          className="text-sm font-medium text-parchment/80"
        >
          Script / Scene Text
        </label>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="text-xs text-amber transition-colors hover:text-amber-light disabled:opacity-40"
        >
          Upload .txt
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,text/plain"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>

      <textarea
        id="script-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="Paste your screenplay or scene description here..."
        rows={18}
        className="script-text w-full resize-y rounded-lg border border-charcoal-light bg-charcoal-light/50 px-4 py-3 text-sm text-parchment placeholder:text-parchment/30 focus:border-amber/50 focus:outline-none focus:ring-1 focus:ring-amber/30 disabled:opacity-50"
      />

      <p className="text-xs text-parchment/40">
        {value.length.toLocaleString()} characters
      </p>
    </div>
  );
}
