import { cn } from "@/lib/utils";

export function Logo({ small }: { small?: boolean }) {
  return (
    <div className={cn("relative grid place-items-center rounded-xl bg-brand shadow-lift", small ? "size-7" : "size-9")}>
      <svg viewBox="0 0 24 24" className={cn("text-primary-foreground", small ? "size-4" : "size-5")} fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
        <path d="M3 12h4l2-5 3 10 2-5h7" />
      </svg>
    </div>
  );
}
