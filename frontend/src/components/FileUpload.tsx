"use client";

import { useCallback, useState, useRef } from "react";
import { Upload, FileText, X, AlertCircle, CheckCircle } from "lucide-react";

interface FileUploadProps {
  onFileSelect: (file: File, content: string) => void;
  disabled?: boolean;
  maxSizeMB?: number;
  acceptedTypes?: string[];
}

interface UploadedFile {
  file: File;
  preview: string;
  status: "pending" | "processing" | "ready" | "error";
  error?: string;
}

export function FileUpload({
  onFileSelect,
  disabled = false,
  maxSizeMB = 10,
  acceptedTypes = [".txt", ".pdf", ".fdx", ".fountain"],
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > maxSizeMB * 1024 * 1024) {
      return `File size exceeds ${maxSizeMB}MB limit`;
    }

    // Check file type
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!acceptedTypes.includes(ext)) {
      return `File type not supported. Accepted: ${acceptedTypes.join(", ")}`;
    }

    return null;
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsText(file);
    });
  };

  const processFile = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setUploadedFile({
        file,
        preview: "",
        status: "error",
        error: validationError,
      });
      return;
    }

    setUploadedFile({
      file,
      preview: "",
      status: "processing",
    });

    try {
      const content = await readFileContent(file);
      const preview = content.substring(0, 500) + (content.length > 500 ? "..." : "");

      setUploadedFile({
        file,
        preview,
        status: "ready",
      });

      onFileSelect(file, content);
    } catch (error) {
      setUploadedFile({
        file,
        preview: "",
        status: "error",
        error: "Failed to read file content",
      });
    }
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (disabled) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        processFile(files[0]);
      }
    },
    [disabled]
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processFile(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleRemove = () => {
    setUploadedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  if (uploadedFile) {
    return (
      <div
        className="rounded-lg p-4"
        style={{
          border: `1px solid ${
            uploadedFile.status === "error"
              ? "var(--flagged)"
              : uploadedFile.status === "ready"
              ? "var(--verified)"
              : "var(--border)"
          }`,
          backgroundColor: "var(--bg)",
        }}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <FileText
              size={20}
              style={{
                color:
                  uploadedFile.status === "error"
                    ? "var(--flagged)"
                    : uploadedFile.status === "ready"
                    ? "var(--verified)"
                    : "var(--text-muted)",
              }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: "var(--text)" }}>
                {uploadedFile.file.name}
              </p>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                {formatFileSize(uploadedFile.file.size)}
              </p>

              {uploadedFile.status === "processing" && (
                <div className="mt-2">
                  <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: "var(--border)" }}>
                    <div
                      className="h-full rounded-full animate-pulse"
                      style={{ backgroundColor: "var(--accent)", width: "60%" }}
                    />
                  </div>
                  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                    Processing file...
                  </p>
                </div>
              )}

              {uploadedFile.status === "error" && uploadedFile.error && (
                <div className="flex items-center gap-1 mt-2">
                  <AlertCircle size={12} style={{ color: "var(--flagged)" }} />
                  <p className="text-xs" style={{ color: "var(--flagged)" }}>
                    {uploadedFile.error}
                  </p>
                </div>
              )}

              {uploadedFile.status === "ready" && (
                <div className="flex items-center gap-1 mt-2">
                  <CheckCircle size={12} style={{ color: "var(--verified)" }} />
                  <p className="text-xs" style={{ color: "var(--verified)" }}>
                    Ready to analyze
                  </p>
                </div>
              )}

              {uploadedFile.preview && (
                <pre
                  className="mt-3 p-2 rounded text-xs overflow-hidden max-h-24"
                  style={{
                    backgroundColor: "var(--bg-secondary, var(--bg))",
                    color: "var(--text-muted)",
                    border: "1px solid var(--border)",
                  }}
                >
                  {uploadedFile.preview}
                </pre>
              )}
            </div>
          </div>

          <button
            onClick={handleRemove}
            className="p-1 rounded hover:opacity-80 transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <X size={16} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        relative rounded-lg border-2 border-dashed p-8 text-center cursor-pointer
        transition-all duration-200
        ${disabled ? "opacity-50 cursor-not-allowed" : "hover:border-opacity-60"}
        ${isDragging ? "border-opacity-100 scale-[1.02]" : ""}
      `}
      style={{
        borderColor: isDragging ? "var(--accent)" : "var(--border)",
        backgroundColor: isDragging
          ? "color-mix(in srgb, var(--accent) 5%, var(--bg))"
          : "var(--bg)",
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedTypes.join(",")}
        onChange={handleFileInput}
        disabled={disabled}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        style={{ cursor: disabled ? "not-allowed" : "pointer" }}
      />

      <Upload
        size={32}
        className="mx-auto mb-3"
        style={{
          color: isDragging ? "var(--accent)" : "var(--text-muted)",
        }}
      />

      <p className="text-sm font-medium mb-1" style={{ color: "var(--text)" }}>
        {isDragging ? "Drop your script here" : "Drag & drop your script"}
      </p>

      <p className="text-xs mb-3" style={{ color: "var(--text-muted)" }}>
        or click to browse
      </p>

      <p className="text-xs" style={{ color: "var(--text-muted)" }}>
        Supported: {acceptedTypes.join(", ").toUpperCase()} (Max {maxSizeMB}MB)
      </p>
    </div>
  );
}
