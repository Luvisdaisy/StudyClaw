"use client";

import { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Upload, Loader2, File } from "lucide-react";
import { documentsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface DocumentUploadProps {
  projectId: string;
}

const ALLOWED_TYPES = [
  "application/pdf",
  "text/markdown",
  "text/plain",
  "text/x-markdown",
];

const ALLOWED_EXTENSIONS = [".pdf", ".md", ".txt"];

export function DocumentUpload({ projectId }: DocumentUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(projectId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents", projectId] });
      setError("");
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const validateFile = (file: File): string | null => {
    const extension = "." + file.name.split(".").pop()?.toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      return `File type not allowed. Allowed types: ${ALLOWED_EXTENSIONS.join(", ")}`;
    }

    if (!ALLOWED_TYPES.includes(file.type) && file.type !== "") {
      return `Invalid file type. Allowed types: ${ALLOWED_TYPES.join(", ")}`;
    }

    return null;
  };

  const handleFile = (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const file = files[0];
    const validationError = validateFile(file);

    if (validationError) {
      setError(validationError);
      return;
    }

    mutation.mutate(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const files = e.dataTransfer.files;
    handleFile(files);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFile(e.target.files);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-4">
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf,.md,.txt"
          onChange={handleChange}
        />

        <div className="flex flex-col items-center gap-3">
          {mutation.isPending ? (
            <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />
          ) : (
            <Upload className="h-10 w-10 text-muted-foreground" />
          )}
          <div>
            <p className="text-sm font-medium">
              {mutation.isPending
                ? "Uploading..."
                : "Drop your file here or click to upload"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Supports PDF, Markdown, and TXT files
            </p>
          </div>
          <Button
            type="button"
            variant="secondary"
            onClick={handleClick}
            disabled={mutation.isPending}
          >
            <File className="mr-2 h-4 w-4" />
            Select File
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {mutation.isError && !error && (
        <Alert variant="destructive">
          <AlertDescription>Failed to upload file. Please try again.</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
