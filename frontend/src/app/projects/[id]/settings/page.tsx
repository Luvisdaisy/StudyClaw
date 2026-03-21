"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { projectsApi } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Github } from "lucide-react";
import { GitHubSettings } from "@/components/github/GitHubSettings";
import { SyncStatus } from "@/components/github/SyncStatus";

export default function SettingsPage() {
  const params = useParams();
  const projectId = params.id as string;

  const { data: project, isLoading, error } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
  });

  if (error) {
    return (
      <div className="flex h-screen">
        <Sidebar projectId={projectId} />
        <main className="flex-1 flex flex-col">
          <Header title="Error" />
          <div className="flex-1 flex items-center justify-center">
            <p className="text-destructive">Failed to load project</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <Sidebar projectId={projectId} projectName={project?.name} />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header title={`${project?.name || "Project"} - Settings`} />
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[200px] w-full" />
            </div>
          ) : (
            <div className="max-w-2xl space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Github className="h-5 w-5" />
                    GitHub Integration
                  </CardTitle>
                  <CardDescription>
                    Connect your project to a GitHub repository for automatic sync
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <GitHubSettings projectId={projectId} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Github className="h-5 w-5" />
                    Repository Sync
                  </CardTitle>
                  <CardDescription>
                    Sync documents from your GitHub repository
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <SyncStatus projectId={projectId} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Project Information</CardTitle>
                  <CardDescription>
                    Details about your project
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Project Name</p>
                    <p className="font-medium">{project?.name}</p>
                  </div>
                  {project?.description && (
                    <div>
                      <p className="text-sm text-muted-foreground">Description</p>
                      <p className="font-medium">{project.description}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-muted-foreground">Created</p>
                    <p className="font-medium">
                      {project?.created_at
                        ? new Date(project.created_at).toLocaleDateString()
                        : "N/A"}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
