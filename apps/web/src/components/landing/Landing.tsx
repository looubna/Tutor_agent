"use client";

import { LandingNav } from "./LandingNav";
import { Hero } from "./Hero";
import { Benefits, Faq, Facts, HowItWorks, LandingFooter, Pricing, Subjects, Testimonials } from "./Sections";
import { Showcase } from "./Showcase";
import { SubjectPicker } from "./SubjectPicker";

export function Landing() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <LandingNav />
      <main className="flex-1">
        <Hero />
        <SubjectPicker />
        <Facts />
        <Benefits />
        <Showcase />
        <Subjects />
        <HowItWorks />
        <Pricing />
        <Testimonials />
        <Faq />
      </main>
      <LandingFooter />
    </div>
  );
}
