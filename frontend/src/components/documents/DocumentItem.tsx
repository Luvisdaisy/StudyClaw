"use client";

import { useState } from "react";
import { FileText, Trash2, Download } from "lucide-react";
import type { Document } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface DocumentItemProps {
  document: Document;
  onDelete: (id: number) => void;
}

export function DocumentItem({ document, onDelete }: DocumentItemProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = () => {
    setIsDeleting(true);
    onDelete(document.id);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getFileTypeLabel = (fileType: string): string => {
    const typeMap: Record<string, string> = {
      "application/pdf": "PDF",
      "text/markdown": "Markdown",
      "text/plain": "Text",
      "text/x-markdown": "Markdown",
    };
    return typeMap[fileType] || fileType.split("/").pop() || "Unknown";
  };

  return (
    <div className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors">
      <div className="flex items-center gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
          <FileText className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium leading-none">{document.filename}</p>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary" className="text-xs">
              {getFileTypeLabel(document.file_type)}
            </Badge>
            <span>{formatFileSize(document.file_size)}</span>
            <span>•</span>
            <span>{new Date(document.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDelete}
          disabled={isDeleting}
          className="text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
