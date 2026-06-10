"use client";

import { AuthGuard } from "@/components/layout/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";
import { ChatWindow } from "@/components/chat/ChatWindow";

export default function ChatPage() {
  return (
    <AuthGuard>
      <div className="flex h-screen">
        <Sidebar />
        <ChatWindow />
      </div>
    </AuthGuard>
  );
}
