import type { Metadata } from "next";
import { LandingNav } from "@/components/landing/LandingNav";
import { PlacementTest } from "@/components/placement/PlacementTest";

export const metadata: Metadata = {
  title: "Placement test — Zanoba",
  description: "Twelve questions to place you on the CEFR ladder, in about five minutes.",
};

export default function PlacementTestPage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <LandingNav />
      <main className="flex-1">
        <PlacementTest />
      </main>
    </div>
  );
}
