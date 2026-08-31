import { redirect } from "next/navigation";
import { Landing } from "@/components/landing/Landing";
import { getSession } from "@/lib/session";

export default async function Home() {
  const session = await getSession();
  if (session?.userId) redirect("/dashboard");
  return <Landing />;
}
