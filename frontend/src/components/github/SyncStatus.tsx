"use client";

import { useRef } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, Loader2, CheckCircle } from "lucide-react";
import { githubApi, type GitHubSyncStatus } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface SyncStatusProps {
  projectId: string;
}

export function SyncStatus({ projectId }: SyncStatusProps) {
  const queryClient = useQueryClient();
  const statusRef = useRef<GitHubSyncStatus | null>(null);

  // Fetch GitHub user to check if connected
  const { data: user } = useQuery({
    queryKey: ["github", "user", projectId],
    queryFn: () => githubApi.getUser(projectId),
    refetchOnWindowFocus: false,
  });

  // Fetch project to check if repo is selected
  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () =>
      fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/projects/${projectId}`)
        .then((res) => res.json()),
    refetchOnWindowFocus: false,
    enabled: !!user,
  });

  // Fetch sync status
  const {
    data: status,
    isLoading: statusLoading,
    error: statusError,
  } = useQuery<GitHubSyncStatus>({
    queryKey: ["github", "sync", "status", projectId],
    queryFn: () => githubApi.getSyncStatus(projectId),
    refetchInterval: () => {
      // Poll more frequently when sync is running
      return statusRef.current?.status === "running" ? 2000 : false;
    },
    refetchIntervalInBackground: false,
  });

  // Keep ref updated with latest status
  if (status) {
    statusRef.current = status;
  }

  const isConnected = !!user;
  const hasRepoSelected = project?.github_repo;
  const canSync = isConnected && hasRepoSelected;
  const isSyncing = status?.status === "running";

  const handleSync = async () => {
    try {
      await githubApi.triggerSync(projectId);
      // Immediately refetch status
      queryClient.invalidateQueries({ queryKey: ["github", "sync", "status", projectId] });
    } catch (err) {
      // Error is handled by the query
    }
  };

  if (!isConnected) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">Sync Status</h3>
        </div>
        <Alert>
          <AlertDescription>
            Connect GitHub and select a repository to enable sync
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!hasRepoSelected) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">Sync Status</h3>
        </div>
        <Alert>
          <AlertDescription>
            Select a repository above to enable sync
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Sync Status</h3>
        <Button
          onClick={handleSync}
          disabled={isSyncing || statusLoading}
          className="gap-2"
        >
          {isSyncing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Syncing...
            </>
          ) : (
            <>
              <RefreshCw className="h-4 w-4" />
              Sync Now
            </>
          )}
        </Button>
      </div>

      {statusError && (
        <Alert variant="destructive">
          <AlertDescription>Failed to load sync status</AlertDescription>
        </Alert>
      )}

      {status?.status === "failed" && status.error && (
        <Alert variant="destructive">
          <AlertDescription>Sync failed: {status.error}</AlertDescription>
        </Alert>
      )}

      {status?.status === "completed" && (
        <Alert className="border-green-500 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            Sync completed successfully
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-4 gap-4">
        <div className="border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold">{status?.status || "idle"}</p>
          <p className="text-xs text-muted-foreground mt-1">Status</p>
        </div>
        <div className="border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold font-mono text-green-600">
            {status?.added ?? "-"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Added</p>
        </div>
        <div className="border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold font-mono text-yellow-600">
            {status?.skipped ?? "-"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Skipped</p>
        </div>
        <div className="border rounded-lg p-3 text-center">
          <p className="text-2xl font-bold font-mono text-red-600">
            {status?.failed ?? "-"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">Failed</p>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Syncs PDF, Markdown, and TXT files from the selected repository.
        Documents with identical content (same hash) will be skipped.
      </p>
    </div>
  );
}
