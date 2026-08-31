import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { TopNav } from "@/components/TopNav";
import { ChatWidget } from "@/components/ChatWidget";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { userId } = await verifySession();
  const user = await prisma.user.findUniqueOrThrow({
    where: { id: userId },
    select: { name: true },
  });

  return (
    <div className="flex min-h-screen w-full flex-col bg-background">
      <TopNav userName={user.name} />
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10 sm:px-8">{children}</main>
      <ChatWidget />
    </div>
  );
}
