"use client";

import Link from "next/link";
import { FolderOpen, Trash2, MoreHorizontal } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Project } from "@/lib/api";

interface ProjectCardProps {
  project: Project;
  onDelete: (id: string) => void;
}

export function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDelete(project.id);
  };

  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="hover:bg-accent/50 transition-colors cursor-pointer h-full">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="flex items-center gap-2">
            <FolderOpen className="h-5 w-5 text-muted-foreground" />
            <h3 className="font-semibold">{project.name}</h3>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger
              className="h-8 w-8 inline-flex items-center justify-center rounded-md hover:bg-accent"
              onClick={(e) => e.preventDefault()}
            >
              <MoreHorizontal className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={handleDelete}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {project.description || "No description"}
          </p>
        </CardContent>
        <CardFooter className="pt-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {project.github_repo && (
              <Badge variant="secondary" className="text-xs">
                GitHub
              </Badge>
            )}
            <span>
              Created {new Date(project.created_at).toLocaleDateString()}
            </span>
          </div>
        </CardFooter>
      </Card>
    </Link>
  );
}
