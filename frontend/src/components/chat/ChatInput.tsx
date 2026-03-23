"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
  enableWebSearch?: boolean;
  onToggleWebSearch?: (enabled: boolean) => void;
}

export function ChatInput({
  onSendMessage,
  isLoading,
  disabled,
  enableWebSearch = false,
  onToggleWebSearch,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim() || isLoading || disabled) return;

    onSendMessage(message.trim());
    setMessage("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2">
      {onToggleWebSearch && (
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className={cn(
            "h-[44px] w-[44px] shrink-0 transition-colors",
            enableWebSearch
              ? "bg-amber-100 text-amber-700 hover:bg-amber-200"
              : "bg-muted text-muted-foreground hover:bg-muted/80"
          )}
          onClick={() => onToggleWebSearch(!enableWebSearch)}
          title={enableWebSearch ? "Disable web search" : "Enable web search"}
        >
          <Globe className="h-4 w-4" />
        </Button>
      )}
      <Textarea
        ref={textareaRef}
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (Shift+Enter for new line)"
        className="min-h-[44px] max-h-[200px] resize-none"
        disabled={isLoading || disabled}
        rows={1}
        maxLength={10000}
      />
      <Button
        type="submit"
        size="icon"
        className="h-[44px] w-[44px] shrink-0"
        disabled={!message.trim() || isLoading || disabled}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </form>
  );
}
