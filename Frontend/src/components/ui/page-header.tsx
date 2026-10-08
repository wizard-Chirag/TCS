import type { ReactNode } from "react";

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
        {subtitle && <p className="mt-1.5 text-muted-foreground">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function EmptyState({ icon, title, children }: { icon: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center rounded-3xl border border-dashed bg-card/50 px-6 py-16 text-center">
      <div className="mb-4 grid size-14 place-items-center rounded-2xl bg-accent text-accent-foreground">{icon}</div>
      <p className="max-w-sm font-medium">{title}</p>
      {children && <div className="mt-5">{children}</div>}
    </div>
  );
}

export const Container = ({ children }: { children: ReactNode }) => (
  <div className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 md:px-8 md:py-10">{children}</div>
);
