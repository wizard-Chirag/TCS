import { createFileRoute, Link } from "@tanstack/react-router";
import { FileSearch, ListChecks, GitCompareArrows, BookOpenText, Stethoscope, ArrowRight } from "lucide-react";
import { Composer } from "@/components/composer";
import { PaperCard } from "@/components/paper-card";
import { Container } from "@/components/page-header";
import { useStore } from "@/lib/store";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "MedBrief AI — Summarize medical literature in seconds" },
      { name: "description", content: "Paste an abstract or upload a PDF to get a structured, source-grounded summary of medical research." },
      { property: "og:title", content: "MedBrief AI — Summarize medical literature in seconds" },
      { property: "og:description", content: "Structured AI summaries of medical papers: objective, methods, findings, limitations." },
    ],
  }),
  component: Home,
});

const quick = [
  { icon: FileSearch, title: "Summarize a Paper", desc: "Full structured brief", to: "/new" },
  { icon: ListChecks, title: "Extract Key Findings", desc: "Numbers and outcomes", to: "/new" },
  { icon: GitCompareArrows, title: "Compare Papers", desc: "Side-by-side evidence", to: "/compare" },
  { icon: BookOpenText, title: "Explain Medical Terms", desc: "Plain-language glossary", to: "/new" },
  { icon: Stethoscope, title: "Find Clinical Insights", desc: "Why findings matter", to: "/new" },
] as const;

function Home() {
  const papers = useStore((s) => s.papers);
  return (
    <Container>
      <section className="mx-auto max-w-3xl pt-4 text-center sm:pt-10">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border bg-surface px-3 py-1 text-xs font-medium text-muted-foreground shadow-soft">
          <span className="size-1.5 rounded-full bg-success" /> Source-grounded research summaries
        </div>
        <h1 className="text-balance text-4xl font-bold tracking-tight sm:text-5xl">
          What would you like to <span className="font-display font-normal italic text-brand">understand</span> today?
        </h1>
        <p className="mt-3 text-lg text-muted-foreground">Summarize medical literature in seconds.</p>
      </section>

      <section className="mx-auto mt-10 max-w-3xl">
        <Composer />
      </section>

      <section className="mx-auto mt-10 grid max-w-5xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        {quick.map(({ icon: Icon, title, desc, to }, i) => (
          <Link
            key={title}
            to={to}
            style={{ animationDelay: `${i * 50}ms` }}
            className="group animate-rise rounded-2xl border bg-card p-4 shadow-soft transition-all hover:-translate-y-0.5 hover:border-primary/25 hover:shadow-lift"
          >
            <div className="mb-3 grid size-9 place-items-center rounded-xl bg-accent text-accent-foreground transition group-hover:bg-brand group-hover:text-primary-foreground">
              <Icon className="size-[18px]" />
            </div>
            <div className="text-sm font-semibold">{title}</div>
            <div className="mt-0.5 text-xs text-muted-foreground">{desc}</div>
          </Link>
        ))}
      </section>

      <section className="mx-auto mt-14 max-w-5xl">
        <div className="mb-4 flex items-end justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight">Recent Research</h2>
            <p className="text-sm text-muted-foreground">Includes sample papers for demonstration.</p>
          </div>
          <Link to="/history" className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline">
            View all history <ArrowRight className="size-4" />
          </Link>
        </div>
        <div className="grid gap-3">
          {papers.slice(0, 4).map((p) => <PaperCard key={p.id} paper={p} />)}
        </div>
      </section>
    </Container>
  );
}
