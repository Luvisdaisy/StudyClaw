"use client";

import { User, Bot } from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}

export function ChatMessage({ role, content, isStreaming }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div
      role="article"
      aria-label={`${isUser ? "User" : "Assistant"} message`}
      className={cn(
        "flex gap-4 py-4",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <Avatar className="h-8 w-8">
        <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-muted"}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "rounded-2xl px-4 py-2 max-w-[80%] text-sm",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        )}
      >
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <p className="whitespace-pre-wrap">
            {(content || "").split("\n").map((line, i) => (
              <span key={i}>
                {line}
                {i < (content || "").split("\n").length - 1 && <br />}
              </span>
            ))}
            {isStreaming && (
              <span className="animate-pulse">▊</span>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
