"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, AlertCircle, PanelLeft, MessageSquare } from "lucide-react";
import { chatApi, documentsApi } from "@/lib/api";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatHistorySidebar } from "./ChatHistorySidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

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
  const [enableWebSearch, setEnableWebSearch] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const streamingContentRef = useRef("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: documents, isLoading: documentsLoading } = useQuery({
    queryKey: ["documents", projectId],
    queryFn: () => documentsApi.list(projectId),
  });

  const { data: sessionData, isLoading: sessionLoading } = useQuery({
    queryKey: ["chat-session", projectId, activeSessionId],
    queryFn: () =>
      activeSessionId ? chatApi.getSession(projectId, activeSessionId) : null,
    enabled: !!activeSessionId,
  });

  const hasDocuments = documents && documents.length > 0;

  // Load session messages when session changes
  useEffect(() => {
    if (sessionData) {
      setMessages(
        sessionData.messages.map((msg, idx) => ({
          id: `${activeSessionId}-${idx}`,
          role: msg.role,
          content: msg.content,
        }))
      );
    } else if (!activeSessionId) {
      setMessages([]);
    }
  }, [sessionData, activeSessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming, streamingContentRef.current]);

  const handleSessionSelect = useCallback(
    (sessionId: string | null) => {
      setActiveSessionId(sessionId);
      if (!sessionId) {
        setMessages([]);
      }
    },
    []
  );

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
        }, enableWebSearch);

        // Invalidate sessions list to reflect new/updated session
        queryClient.invalidateQueries({ queryKey: ["chat-sessions", projectId] });
      } catch (err) {
        if (!err || !(err instanceof Error && err.message === "Response buffer overflow")) {
          setError("Failed to send message. Please try again.");
        }
      } finally {
        setIsStreaming(false);
      }
    },
    [projectId, enableWebSearch, queryClient]
  );

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <div
        className={cn(
          "flex-shrink-0 transition-all duration-300 ease-out",
          sidebarOpen ? "w-72" : "w-0"
        )}
      >
        {sidebarOpen && (
          <ChatHistorySidebar
            projectId={projectId}
            activeSessionId={activeSessionId}
            onSessionSelect={handleSessionSelect}
          />
        )}
      </div>

      {/* Toggle sidebar button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className={cn(
          "absolute top-4 z-10 flex items-center justify-center",
          "w-8 h-8 rounded-lg border border-stone-300/50 bg-white/80 backdrop-blur-sm",
          "shadow-sm hover:bg-stone-50 hover:border-stone-400",
          "transition-all duration-200",
          sidebarOpen ? "left-[280px]" : "left-4"
        )}
        aria-label={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
      >
        <PanelLeft
          className={cn(
            "h-4 w-4 transition-transform duration-200",
            sidebarOpen ? "text-amber-700" : "text-stone-500"
          )}
        />
      </button>

      {/* Main chat area */}
      <div className="flex flex-col flex-1 h-full">
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
            {documentsLoading || sessionLoading ? (
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
                <div className="rounded-full bg-gradient-to-br from-amber-50 to-stone-100 p-4 shadow-sm border border-amber-100/50">
                  <MessageSquare className="h-8 w-8 text-amber-600" />
                </div>
                <h3 className="mt-4 text-lg font-heading font-medium text-stone-800">
                  {activeSessionId ? "Conversation loaded" : "Start a conversation"}
                </h3>
                <p className="mt-2 text-sm text-stone-500 max-w-md">
                  {activeSessionId
                    ? "Continue your conversation or start a new one."
                    : "Ask questions about your uploaded documents and get AI-powered answers."}
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

        <div className="border-t border-stone-200/60 p-4 bg-gradient-to-t from-stone-50/50 to-white/80 backdrop-blur-sm">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isStreaming}
              disabled={!hasDocuments}
              enableWebSearch={enableWebSearch}
              onToggleWebSearch={setEnableWebSearch}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
