"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FolderOpen, Settings, FileText, MessageSquare } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

interface SidebarProps {
  projectId?: string;
  projectName?: string;
}

export function Sidebar({ projectId, projectName }: SidebarProps) {
  const pathname = usePathname();

  const mainNavItems = projectId
    ? [
        {
          title: "Chat",
          href: `/projects/${projectId}`,
          icon: MessageSquare,
        },
        {
          title: "Documents",
          href: `/projects/${projectId}/documents`,
          icon: FileText,
        },
        {
          title: "Settings",
          href: `/projects/${projectId}/settings`,
          icon: Settings,
        },
      ]
    : [];

  return (
    <aside className="w-64 border-r bg-card h-full flex flex-col">
      <div className="p-4 border-b">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <FolderOpen className="h-5 w-5" />
          <span>StudyClaw</span>
        </Link>
      </div>

      {projectId && projectName && (
        <div className="p-4 border-b">
          <DropdownMenu>
            <DropdownMenuTrigger className="w-full justify-start gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent">
              <FolderOpen className="h-4 w-4" />
              <span className="truncate">{projectName}</span>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem>
                <Link href="/">Switch Project</Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}

      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {mainNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-accent hover:text-accent-foreground",
                    isActive ? "bg-accent text-accent-foreground" : "text-muted-foreground"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.title}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-4 border-t">
        <div className="flex items-center gap-2">
          <Avatar className="h-8 w-8">
            <AvatarFallback>U</AvatarFallback>
          </Avatar>
          <div className="text-sm">
            <p className="font-medium">User</p>
            <p className="text-xs text-muted-foreground">Local Mode</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
