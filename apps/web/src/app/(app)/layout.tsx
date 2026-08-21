import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { Sidebar } from "@/components/Sidebar";
import { ChatWidget } from "@/components/ChatWidget";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { userId } = await verifySession();
  const user = await prisma.user.findUniqueOrThrow({
    where: { id: userId },
    select: { name: true },
  });

  return (
    <div className="flex min-h-screen w-full bg-background">
      <Sidebar userName={user.name} />
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-end gap-2 px-8 pt-6">
          <ThemeToggle variant="light" />
          <LanguageToggle variant="light" />
        </header>
        <main className="flex-1 px-8 py-8">{children}</main>
      </div>
      <ChatWidget />
    </div>
  );
}
