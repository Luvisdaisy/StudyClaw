"use client";

import { Menu, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CreateProjectDialog } from "@/components/projects/CreateProjectDialog";

interface HeaderProps {
  title: string;
  showCreateButton?: boolean;
}

export function Header({ title, showCreateButton = false }: HeaderProps) {
  return (
    <header className="border-b bg-card">
      <div className="flex items-center justify-between px-6 py-4">
        <h1 className="text-xl font-semibold">{title}</h1>
        <div className="flex items-center gap-2">
          {showCreateButton && <CreateProjectDialog />}
        </div>
      </div>
    </header>
  );
}
