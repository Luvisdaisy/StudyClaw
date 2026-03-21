"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ProjectList } from "@/components/projects/ProjectList";

export default function HomePage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header title="Projects" showCreateButton />
        <div className="flex-1 overflow-y-auto p-6">
          <ProjectList />
        </div>
      </main>
    </div>
  );
}
