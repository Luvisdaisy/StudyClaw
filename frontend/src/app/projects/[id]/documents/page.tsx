"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { projectsApi } from "@/lib/api";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { DocumentList } from "@/components/documents/DocumentList";
import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentsPage() {
  const params = useParams();
  const projectId = params.id as string;

  const { data: project, isLoading, error } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => projectsApi.get(projectId),
  });

  if (error) {
    return (
      <div className="flex h-screen">
        <Sidebar projectId={projectId} projectName={project?.name} />
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
        <Header title={`${project?.name || "Project"} - Documents`} />
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[150px] w-full" />
              <Skeleton className="h-[72px] w-full" />
              <Skeleton className="h-[72px] w-full" />
            </div>
          ) : (
            <DocumentList projectId={projectId} />
          )}
        </div>
      </main>
    </div>
  );
}
