"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Github, Loader2, LogOut, Check } from "lucide-react";
import { githubApi, type GitHubRepo } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface GitHubSettingsProps {
  projectId: string;
}

export function GitHubSettings({ projectId }: GitHubSettingsProps) {
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [selectedRepo, setSelectedRepo] = useState("");
  const queryClient = useQueryClient();

  // Fetch connected user
  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ["github", "user", projectId],
    queryFn: () => githubApi.getUser(projectId),
    refetchOnWindowFocus: false,
  });

  // Fetch repos list
  const {
    data: repos,
    isLoading: reposLoading,
    error: reposError,
  } = useQuery({
    queryKey: ["github", "repos", projectId],
    queryFn: () => githubApi.listRepos(projectId),
    enabled: !!user,
    refetchOnWindowFocus: false,
  });

  // Connect mutation
  const connectMutation = useMutation({
    mutationFn: (token: string) => githubApi.connect(projectId, token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github", "user", projectId] });
      setToken("");
      setError("");
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Disconnect mutation
  const disconnectMutation = useMutation({
    mutationFn: () => githubApi.disconnect(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github", "user", projectId] });
      queryClient.invalidateQueries({ queryKey: ["github", "repos", projectId] });
      setSelectedRepo("");
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  // Select repo mutation
  const selectRepoMutation = useMutation({
    mutationFn: (repoFullName: string) => {
      const repo = repos?.find((r) => r.full_name === repoFullName);
      return githubApi.selectRepo(projectId, repoFullName, repo?.default_branch || "main");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleConnect = () => {
    if (!token.trim()) {
      setError("Please enter a GitHub token");
      return;
    }
    connectMutation.mutate(token.trim());
  };

  const handleDisconnect = () => {
    disconnectMutation.mutate();
  };

  const handleRepoSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedRepo(value);
    if (value) {
      selectRepoMutation.mutate(value);
    }
  };

  const isConnected = !!user;

  return (
    <div className="space-y-4">
      {!isConnected ? (
        // Not connected - show PAT input
        <div className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="github-token" className="text-sm font-medium">
              GitHub Personal Access Token
            </label>
            <Input
              id="github-token"
              type="password"
              placeholder="ghp_xxxxxxxxxxxx"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              disabled={connectMutation.isPending}
            />
            <p className="text-xs text-muted-foreground">
              Create a PAT at GitHub Settings → Developer settings → Personal access tokens.
              Required scopes: repo (for private repos) or public_repo (for public only).
            </p>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleConnect}
            disabled={connectMutation.isPending}
            className="gap-2"
          >
            {connectMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Connecting...
              </>
            ) : (
              <>
                <Github className="h-4 w-4" />
                Connect GitHub
              </>
            )}
          </Button>
        </div>
      ) : (
        // Connected - show user info and repo selector
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-3 border rounded-lg bg-muted/50">
            {user.avatar_url && (
              <img
                src={user.avatar_url}
                alt={user.login}
                className="h-10 w-10 rounded-full"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">
                {user.name || user.login}
              </p>
              <p className="text-sm text-muted-foreground truncate">
                @{user.login}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDisconnect}
              disabled={disconnectMutation.isPending}
              className="gap-1.5 text-destructive hover:text-destructive"
            >
              {disconnectMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <LogOut className="h-4 w-4" />
              )}
              Disconnect
            </Button>
          </div>

          {reposLoading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading repositories...
            </div>
          ) : reposError ? (
            <Alert variant="destructive">
              <AlertDescription>Failed to load repositories</AlertDescription>
            </Alert>
          ) : repos && repos.length > 0 ? (
            <div className="space-y-2">
              <label htmlFor="repo-select" className="text-sm font-medium">
                Select Repository
              </label>
              <select
                id="repo-select"
                value={selectedRepo}
                onChange={handleRepoSelect}
                disabled={selectRepoMutation.isPending}
                className="w-full h-9 rounded-lg border border-input bg-transparent px-3 py-1 text-sm transition-colors focus:border-ring focus:ring-3 focus:ring-ring/50 disabled:opacity-50"
              >
                <option value="">Select a repository...</option>
                {repos.map((repo: GitHubRepo) => (
                  <option key={repo.full_name} value={repo.full_name}>
                    {repo.full_name}
                  </option>
                ))}
              </select>
              {selectRepoMutation.isPending && (
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Saving selection...
                </p>
              )}
              {selectRepoMutation.isSuccess && (
                <p className="text-xs text-green-600 flex items-center gap-1">
                  <Check className="h-3 w-3" />
                  Repository selected
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No repositories found</p>
          )}
        </div>
      )}
    </div>
  );
}
