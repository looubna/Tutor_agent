import { CourseRail } from "@/components/CourseRail";

/** Subjects on the left, whichever course you're reading in the middle. */
export default function CourseLayout({ children }: LayoutProps<"/course">) {
  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 lg:flex-row lg:items-start">
      <CourseRail />
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}
