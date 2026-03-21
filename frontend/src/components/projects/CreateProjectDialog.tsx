"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { projectsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export function CreateProjectDialog() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [githubRepo, setGithubRepo] = useState("");
  const [error, setError] = useState("");

  const router = useRouter();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () =>
      projectsApi.create({
        name,
        description: description || undefined,
        github_repo: githubRepo || undefined,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
      setName("");
      setDescription("");
      setGithubRepo("");
      router.push(`/projects/${data.id}`);
    },
    onError: (err: Error) => {
      setError(err.message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("Project name is required");
      return;
    }

    // Validate GitHub repo format if provided
    if (githubRepo && !/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(githubRepo)) {
      setError("Invalid GitHub repository format. Use owner/repo format.");
      return;
    }

    mutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger className="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground px-4 py-2">
        <Plus className="mr-2 h-4 w-4" />
        New Project
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Create a new project to organize your documents and chat conversations.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="name" className="text-sm font-medium">
              Project Name
            </label>
            <Input
              id="name"
              placeholder="My Study Project"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={200}
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium">
              Description (optional)
            </label>
            <Textarea
              id="description"
              placeholder="A brief description of your project..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={1000}
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="github_repo" className="text-sm font-medium">
              GitHub Repository (optional)
            </label>
            <Input
              id="github_repo"
              placeholder="owner/repo"
              value={githubRepo}
              onChange={(e) => setGithubRepo(e.target.value)}
              maxLength={200}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Creating..." : "Create Project"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
