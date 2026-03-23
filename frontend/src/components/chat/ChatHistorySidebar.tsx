"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, MessageSquare, Trash2, Clock, Loader2 } from "lucide-react";
import { chatApi, SessionSummary } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

interface ChatHistorySidebarProps {
  projectId: string;
  activeSessionId: string | null;
  onSessionSelect: (sessionId: string | null) => void;
}

function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "";

  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) return "Just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`;

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function SessionItem({
  session,
  isActive,
  onSelect,
  onDelete,
}: {
  session: SessionSummary;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  return (
    <>
      <button
        onClick={onSelect}
        className={cn(
          "group relative w-full text-left px-3 py-3 rounded-lg transition-all duration-200",
          "border border-transparent",
          "hover:bg-amber-50/80",
          isActive && "bg-amber-50 border-amber-200/60"
        )}
      >
        <div className="flex items-start gap-2.5">
          <div
            className={cn(
              "mt-0.5 flex-shrink-0 rounded-md p-1.5",
              isActive ? "bg-amber-200/70" : "bg-stone-200/60 group-hover:bg-stone-200"
            )}
          >
            <MessageSquare
              className={cn(
                "h-3.5 w-3.5",
                isActive ? "text-amber-800" : "text-stone-500"
              )}
            />
          </div>

          <div className="flex-1 min-w-0">
            <p
              className={cn(
                "text-sm font-medium leading-tight line-clamp-1",
                isActive ? "text-amber-900" : "text-stone-700 group-hover:text-stone-900"
              )}
            >
              {session.title || "Untitled conversation"}
            </p>
            {session.updated_at && (
              <p className="flex items-center gap-1 mt-1 text-xs text-stone-400">
                <Clock className="h-3 w-3" />
                {formatRelativeTime(session.updated_at)}
              </p>
            )}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowDeleteDialog(true);
            }}
            className={cn(
              "flex-shrink-0 opacity-0 group-hover:opacity-100 p-1 rounded-md",
              "transition-all duration-150",
              "hover:bg-red-100 hover:text-red-600",
              "focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-200"
            )}
            aria-label="Delete conversation"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </button>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-heading">Delete conversation?</DialogTitle>
            <DialogDescription>
              This will permanently delete "{session.title || "Untitled conversation"}" and
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              className="border-stone-300"
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={(e) => {
                e.stopPropagation();
                setShowDeleteDialog(false);
                onDelete(e);
              }}
            >
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function EmptyState({ onNewChat }: { onNewChat: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="relative mb-4">
        <div className="absolute inset-0 bg-amber-100 rounded-full blur-xl opacity-60" />
        <div className="relative bg-amber-50 rounded-full p-4 border border-amber-200/50">
          <MessageSquare className="h-8 w-8 text-amber-600" />
        </div>
      </div>
      <h3 className="font-heading text-lg font-medium text-stone-800 mb-1">
        No conversations yet
      </h3>
      <p className="text-sm text-stone-500 mb-4 max-w-[200px]">
        Start a new conversation to explore your documents
      </p>
      <Button
        onClick={onNewChat}
        size="sm"
        className="bg-amber-700 hover:bg-amber-800 text-amber-50"
      >
        <Plus className="h-4 w-4 mr-1.5" />
        New conversation
      </Button>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-2 p-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-start gap-2.5">
          <Skeleton className="h-8 w-8 rounded-md bg-stone-200" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-4 w-3/4 rounded bg-stone-200" />
            <Skeleton className="h-3 w-1/2 rounded bg-stone-100" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function ChatHistorySidebar({
  projectId,
  activeSessionId,
  onSessionSelect,
}: ChatHistorySidebarProps) {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["chat-sessions", projectId],
    queryFn: () => chatApi.listSessions(projectId),
  });

  const deleteMutation = useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteSession(projectId, sessionId),
    onSuccess: (_, deletedSessionId) => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions", projectId] });
      if (activeSessionId === deletedSessionId) {
        onSessionSelect(null);
      }
    },
  });

  const handleNewChat = () => {
    onSessionSelect(null);
  };

  const handleDeleteSession = (sessionId: string) => (e: React.MouseEvent) => {
    e.stopPropagation();
    deleteMutation.mutate(sessionId);
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-stone-50/50 to-stone-100/30 border-r border-stone-200/60">
      {/* Header */}
      <div className="flex-shrink-0 px-3 py-4 border-b border-stone-200/50 bg-gradient-to-r from-amber-50/30 to-transparent">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-heading text-lg font-semibold text-stone-800 tracking-tight">
              Conversations
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              {data?.total ? `${data.total} session${data.total !== 1 ? "s" : ""}` : ""}
            </p>
          </div>
          <Button
            onClick={handleNewChat}
            size="sm"
            variant="ghost"
            className="text-stone-600 hover:text-amber-700 hover:bg-amber-50"
          >
            <Plus className="h-4 w-4 mr-1" />
            New
          </Button>
        </div>
      </div>

      {/* Session List */}
      <ScrollArea className="flex-1 py-2">
        {isLoading ? (
          <LoadingSkeleton />
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <div className="bg-red-50 rounded-full p-3 mb-3">
              <Trash2 className="h-5 w-5 text-red-400" />
            </div>
            <p className="text-sm text-stone-600">Failed to load sessions</p>
            <Button
              variant="link"
              size="sm"
              onClick={() => queryClient.invalidateQueries({ queryKey: ["chat-sessions", projectId] })}
              className="text-amber-600 hover:text-amber-700 mt-1"
            >
              Try again
            </Button>
          </div>
        ) : data?.sessions.length === 0 ? (
          <EmptyState onNewChat={handleNewChat} />
        ) : (
          <div className="space-y-1 px-2">
            {data?.sessions.map((session) => (
              <SessionItem
                key={session.session_id}
                session={session}
                isActive={activeSessionId === session.session_id}
                onSelect={() => onSessionSelect(session.session_id)}
                onDelete={handleDeleteSession(session.session_id)}
              />
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Footer */}
      {data?.sessions && data.sessions.length > 0 && (
        <div className="flex-shrink-0 px-3 py-3 border-t border-stone-200/50 bg-gradient-to-t from-stone-100/50 to-transparent">
          <Button
            onClick={handleNewChat}
            variant="outline"
            className={cn(
              "w-full justify-start gap-2",
              "border-stone-300/70 bg-white/60 backdrop-blur-sm",
              "hover:bg-amber-50 hover:border-amber-300 hover:text-amber-800",
              "transition-all duration-200"
            )}
          >
            <Plus className="h-4 w-4 text-amber-600" />
            <span className="text-stone-700">New conversation</span>
          </Button>
        </div>
      )}
    </div>
  );
}
