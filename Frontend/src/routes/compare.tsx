import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Check, Plus, Bot, Equal, GitBranch, Zap, Scale } from "lucide-react";
import { Container, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import type { Paper } from "@/lib/types";

export const Route = createFileRoute("/compare")({
  head: () => ({
    meta: [
      { title: "Compare Papers — MedBrief AI" },
      { name: "description", content: "Compare 2–4 medical papers side by side: design, population, outcomes and findings." },
      { property: "og:title", content: "Compare Papers — MedBrief AI" },
      { property: "og:description", content: "Side-by-side comparison of medical research papers." },
    ],
  }),
  component: Compare,
});

const rows: { label: string; get: (p: Paper) => React.ReactNode }[] = [
  { label: "Study Design", get: (p) => p.compare.design },
  { label: "Population", get: (p) => p.compare.population },
  { label: "Sample Size", get: (p) => p.compare.sampleSize },
  { label: "Intervention", get: (p) => p.compare.intervention },
  { label: "Primary Outcome", get: (p) => p.compare.outcome },
  { label: "Key Findings", get: (p) => <ul className="space-y-1">{p.summary.findings.slice(0, 2).map((f) => <li key={f}>• {f}</li>)}</ul> },
  { label: "Limitations", get: (p) => p.summary.limitations[0] },
  { label: "Conclusion", get: (p) => p.summary.conclusion },
];

function Compare() {
  const papers = useStore((s) => s.papers);
  const [sel, setSel] = useState<string[]>(papers.slice(0, 2).map((p) => p.id).concat(papers[2] ? [papers[2].id] : []));
  const chosen = sel.map((id) => papers.find((p) => p.id === id)).filter(Boolean) as Paper[];

  const toggle = (id: string) =>
    setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : s.length >= 4 ? s : [...s, id]));

  const designs = new Set(chosen.map((p) => p.compare.design));

  return (
    <Container>
      <PageHeader title="Compare Papers" subtitle="Select 2–4 papers to compare side by side." actions={<Button asChild variant="soft"><Link to="/new"><Plus /> Upload new</Link></Button>} />
      <div className="mb-6 flex flex-wrap gap-2">
        {papers.map((p) => {
          const on = sel.includes(p.id);
          return (
            <button key={p.id} onClick={() => toggle(p.id)} className={cn("flex max-w-xs items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition", on ? "border-primary bg-accent text-accent-foreground" : "bg-surface text-muted-foreground hover:border-primary/40")}>
              <span className={cn("grid size-4 shrink-0 place-items-center rounded-full border", on && "border-primary bg-primary text-primary-foreground")}>{on && <Check className="size-3" />}</span>
              <span className="truncate">{p.title}</span>
            </button>
          );
        })}
      </div>

      {chosen.length < 2 ? (
        <div className="rounded-2xl border border-dashed p-10 text-center text-muted-foreground">Select at least two papers to compare.</div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-2xl border bg-card shadow-soft">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="w-40 p-4 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground" />
                  {chosen.map((p, i) => (
                    <th key={p.id} className="p-4 text-left align-top">
                      <div className="text-xs font-bold text-primary">Paper {i + 1}</div>
                      <Link to="/paper/$id" params={{ id: p.id }} className="mt-0.5 line-clamp-2 font-semibold hover:text-primary">{p.title}</Link>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.label} className="border-b last:border-0">
                    <td className="p-4 align-top text-xs font-bold uppercase tracking-wider text-muted-foreground">{r.label}</td>
                    {chosen.map((p) => <td key={p.id} className="p-4 align-top leading-relaxed">{r.get(p)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <section className="mt-8">
            <h2 className="mb-1 flex items-center gap-2 text-lg font-bold"><Bot className="size-5 text-primary" /> AI Comparative Analysis</h2>
            <p className="mb-4 text-xs text-muted-foreground">Demo analysis generated from the summaries above. Verify against original publications.</p>
            <div className="grid gap-4 md:grid-cols-2">
              <Card icon={Equal} title="Similarities">All selected papers report outcomes from {chosen.map((p) => p.compare.population.toLowerCase()).join("; ")}, and each acknowledges limitations that affect generalizability.</Card>
              <Card icon={GitBranch} title="Differences">Study designs differ ({[...designs].join(", ")}), as do sample sizes ({chosen.map((p) => p.compare.sampleSize).join(" vs ")}), which affects strength of evidence.</Card>
              <Card icon={Zap} title="Conflicting findings">No direct contradictions were detected between the summarized conclusions; the papers address different questions or populations.</Card>
              <Card icon={Scale} title="Overall evidence picture">Randomized and meta-analytic evidence should be weighted above observational and model-development studies. Prospective validation remains a common gap.</Card>
            </div>
          </section>
        </>
      )}
    </Container>
  );
}

function Card({ icon: Icon, title, children }: { icon: typeof Equal; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border bg-card p-5 shadow-soft">
      <div className="mb-2 flex items-center gap-2 text-sm font-bold"><Icon className="size-4 text-primary" /> {title}</div>
      <p className="text-sm leading-relaxed text-muted-foreground">{children}</p>
    </div>
  );
}
