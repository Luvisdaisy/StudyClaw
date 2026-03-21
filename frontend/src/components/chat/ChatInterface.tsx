"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, AlertCircle } from "lucide-react";
import { chatApi, documentsApi } from "@/lib/api";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";

const MAX_STREAMING_BUFFER_SIZE = 1024 * 1024; // 1MB limit

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  projectId: string;
}

export function ChatInterface({ projectId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamingContentRef = useRef("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentsApi.list(projectId),
  });

  const hasDocuments = documents && documents.length > 0;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming, streamingContentRef.current]);

  const handleSendMessage = useCallback(
    async (message: string) => {
      const userMessageId = Date.now().toString();
      const assistantMessageId = (Date.now() + 1).toString();

      // Add user message
      setMessages((prev) => [
        ...prev,
        { id: userMessageId, role: "user", content: message },
      ]);

      // Add empty assistant message placeholder
      setMessages((prev) => [
        ...prev,
        { id: assistantMessageId, role: "assistant", content: "" },
      ]);

      setIsStreaming(true);
      setError(null);
      streamingContentRef.current = "";

      try {
        await chatApi.sendMessage(projectId, message, (chunk) => {
          // Check buffer size limit to prevent memory exhaustion
          if (streamingContentRef.current.length + chunk.length > MAX_STREAMING_BUFFER_SIZE) {
            setError("Response too large. Please try a shorter message.");
            throw new Error("Response buffer overflow");
          }
          streamingContentRef.current += chunk;
          // Update the assistant message with accumulated content
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: streamingContentRef.current }
                : msg
            )
          );
        });
      } catch (err) {
        if (!err || !(err instanceof Error && err.message === "Response buffer overflow")) {
          setError("Failed to send message. Please try again.");
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [projectId]
  );

  return (
    <div className="flex flex-col h-full">
      {!hasDocuments && !documentsLoading && (
        <Alert className="m-4">
          <FileText className="h-4 w-4" />
          <AlertDescription>
            Upload some documents first to enable chat functionality.
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <ScrollArea className="flex-1 px-4" ref={scrollAreaRef}>
        <div className="max-w-3xl mx-auto">
          {documentsLoading ? (
            <div className="space-y-4 pt-4">
              <div className="flex gap-4">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-20 w-2/3" />
              </div>
              <div className="flex gap-4 flex-row-reverse">
                <Skeleton className="h-8 w-8 rounded-full" />
                <Skeleton className="h-20 w-2/3" />
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="rounded-full bg-muted p-4">
                <FileText className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="mt-4 text-lg font-medium">Start a conversation</h3>
              <p className="mt-2 text-sm text-muted-foreground max-w-md">
                Ask questions about your uploaded documents and get AI-powered
                answers.
              </p>
            </div>
          ) : (
            <div className="space-y-0">
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  isStreaming={isStreaming && message.id === messages[messages.length - 1]?.id}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t p-4 bg-background">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isStreaming}
            disabled={!hasDocuments}
          />
        </div>
      </div>
    </div>
  );
}
