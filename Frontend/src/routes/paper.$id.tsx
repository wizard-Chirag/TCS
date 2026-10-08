import { createFileRoute, Link } from "@tanstack/react-router";
import { useRef, useState, useEffect } from "react";
import {
  Bookmark, Share2, Download, Copy, Target, FlaskConical, BarChart3, CheckCircle2, HeartPulse, AlertTriangle,
  Lightbulb, ShieldCheck, Send, Loader2, ArrowLeft, Bot, Info,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Container, EmptyState } from "@/components/page-header";
import { FavoriteButton } from "@/components/paper-card";
import { fileLabel } from "@/components/file-icon";
import { actions, useStore } from "@/lib/store";
import { askPaper } from "@/lib/mock-ai";
import { formatDate } from "@/lib/format";
import type { Paper } from "@/lib/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/paper/$id")({
  head: () => ({
    meta: [
      { title: "Paper Summary — MedBrief AI" },
      { name: "description", content: "Structured AI summary with key findings, limitations and an ask-the-paper assistant." },
      { property: "og:title", content: "Paper Summary — MedBrief AI" },
      { property: "og:description", content: "Structured AI summary of a medical research paper." },
    ],
  }),
  component: PaperPage,
});

function Section({ icon: Icon, title, children, tone = "primary" }: { icon: typeof Target; title: string; children: React.ReactNode; tone?: "primary" | "teal" | "success" | "warning" }) {
  const tones = { primary: "bg-primary/10 text-primary", teal: "bg-teal/10 text-teal", success: "bg-success/10 text-success", warning: "bg-warning/15 text-warning" };
  return (
    <section className="rounded-2xl border bg-card p-5 shadow-soft sm:p-6">
      <div className="mb-3 flex items-center gap-2.5">
        <div className={cn("grid size-8 place-items-center rounded-lg", tones[tone])}><Icon className="size-4" /></div>
        <h3 className="text-xs font-bold uppercase tracking-[0.12em] text-muted-foreground">{title}</h3>
      </div>
      <div className="text-[15px] leading-relaxed">{children}</div>
    </section>
  );
}

function toText(p: Paper) {
  const s = p.summary;
  return `${p.title}\n\nEXECUTIVE SUMMARY\n${s.executive}\n\nOBJECTIVE\n${s.objective}\n\nMETHODOLOGY\n${s.methodology.map((m) => `${m.label}: ${m.value}`).join("\n")}\n\nKEY FINDINGS\n${s.findings.map((f) => `- ${f}`).join("\n")}\n\nCONCLUSION\n${s.conclusion}\n\nCLINICAL SIGNIFICANCE\n${s.clinical}\n\nLIMITATIONS\n${s.limitations.map((f) => `- ${f}`).join("\n")}\n\nAI-generated summary. Verify important findings against the original publication.`;
}

function PaperPage() {
  const { id } = Route.useParams();
  const paper = useStore((s) => s.papers.find((p) => p.id === id));
  if (!paper)
    return (
      <Container>
        <EmptyState icon={<Info />} title="This summary could not be found.">
          <Button asChild variant="hero"><Link to="/">Back home</Link></Button>
        </EmptyState>
      </Container>
    );
  const s = paper.summary;

  const download = () => {
    const blob = new Blob([toText(paper)], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${paper.title.slice(0, 50)}.txt`;
    a.click();
    toast.success("Summary downloaded");
  };

  return (
    <Container>
      <Link to="/history" className="mb-5 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary">
        <ArrowLeft className="size-4" /> All summaries
      </Link>

      <header className="mb-8">
        <div className="mb-3 flex flex-wrap gap-2">
          {paper.sample && <Badge variant="outline" className="rounded-full">Demo content</Badge>}
          <Badge variant="secondary" className="rounded-full">{fileLabel(paper.fileType)}</Badge>
          {paper.tags.map((t) => <Badge key={t} variant="secondary" className="rounded-full">{t}</Badge>)}
        </div>
        <h1 className="max-w-4xl text-balance text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{paper.title}</h1>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-muted-foreground">
          <span>{paper.authors}</span>
          <span className="italic">{paper.journal}</span>
          <span>{formatDate(paper.published)}</span>
          {paper.pmid && <span>PMID: {paper.pmid}</span>}
          {paper.doi && <span>DOI: {paper.doi}</span>}
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          <Button variant="soft" onClick={() => { actions.toggleSaved(paper.id); toast.success(paper.saved ? "Removed from saved" : "Saved to library"); }}>
            <Bookmark className={cn(paper.saved && "fill-primary text-primary")} /> {paper.saved ? "Saved" : "Save"}
          </Button>
          <Button variant="soft" onClick={() => { navigator.clipboard.writeText(window.location.href); toast.success("Link copied"); }}><Share2 /> Share</Button>
          <Button variant="soft" onClick={download}><Download /> Download</Button>
          <div className="rounded-full border bg-surface shadow-soft"><FavoriteButton paper={paper} /></div>
        </div>
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <div className="space-y-5">
          <section className="relative overflow-hidden rounded-3xl border bg-card p-6 shadow-lift sm:p-8">
            <div aria-hidden className="absolute inset-x-0 top-0 h-1 bg-brand" />
            <div className="mb-3 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-sm font-bold text-primary"><Bot className="size-4" /> AI Executive Summary</h2>
              <Button variant="ghost" size="sm" className="rounded-full" onClick={() => { navigator.clipboard.writeText(toText(paper)); toast.success("Summary copied"); }}>
                <Copy /> Copy
              </Button>
            </div>
            <p className="font-display text-xl leading-relaxed sm:text-2xl">{s.executive}</p>
          </section>

          <div className="grid gap-5 md:grid-cols-2">
            <Section icon={Target} title="Objective">{s.objective}</Section>
            <Section icon={CheckCircle2} title="Conclusion" tone="success">{s.conclusion}</Section>
          </div>

          <Section icon={FlaskConical} title="Methodology" tone="teal">
            <dl className="grid gap-3 sm:grid-cols-2">
              {s.methodology.map((m) => (
                <div key={m.label} className="rounded-xl bg-muted/60 p-3">
                  <dt className="text-xs font-medium text-muted-foreground">{m.label}</dt>
                  <dd className="mt-0.5 text-sm font-semibold">{m.value}</dd>
                </div>
              ))}
            </dl>
          </Section>

          <Section icon={BarChart3} title="Key Findings">
            <ul className="space-y-2.5">
              {s.findings.map((f) => (
                <li key={f} className="flex gap-3"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />{f}</li>
              ))}
            </ul>
          </Section>

          <Section icon={HeartPulse} title="Clinical Significance" tone="teal">
            {s.clinical}
            <p className="mt-2 text-xs text-muted-foreground">Not personalized medical advice.</p>
          </Section>

          <Section icon={AlertTriangle} title="Limitations" tone="warning">
            <ul className="space-y-2">
              {s.limitations.map((f) => <li key={f} className="flex gap-3"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-warning" />{f}</li>)}
            </ul>
          </Section>

          <div>
            <h3 className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.12em] text-muted-foreground"><Lightbulb className="size-4 text-primary" /> Key Takeaways</h3>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {s.takeaways.map((t, i) => (
                <div key={t} className="rounded-2xl border bg-gradient-to-br from-accent to-card p-4 shadow-soft">
                  <div className="text-brand text-2xl font-bold">0{i + 1}</div>
                  <p className="mt-1 text-sm font-medium leading-snug">{t}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <aside className="space-y-5 lg:sticky lg:top-20 lg:self-start">
          <section className="rounded-2xl border bg-card p-5 shadow-soft">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-bold"><ShieldCheck className="size-4 text-success" /> AI Analysis</h3>
            <dl className="space-y-2.5 text-sm">
              <Row k="Summary confidence" v="Source-grounded summary" />
              <Row k="Sections analyzed" v={`${7} sections`} />
              <Row k="Source document" v={paper.fileName ?? paper.journal} />
              <Row k="Processing status" v={<span className="inline-flex items-center gap-1.5 text-success"><span className="size-1.5 rounded-full bg-success" /> Complete</span>} />
            </dl>
            <p className="mt-4 rounded-xl bg-muted p-3 text-xs leading-relaxed text-muted-foreground">
              AI-generated summary. Verify important findings against the original publication.
            </p>
          </section>
          <AskPanel paper={paper} />
        </aside>
      </div>
    </Container>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="max-w-[60%] truncate text-right font-medium">{v}</dd>
    </div>
  );
}

const SUGGESTED = ["What were the main findings?", "What was the study population?", "What are the limitations?", "Explain the results in simple terms.", "How does this compare with previous research?"];

function AskPanel({ paper }: { paper: Paper }) {
  const [msgs, setMsgs] = useState<{ role: "user" | "ai"; text: string }[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }), [msgs, busy]);

  const ask = async (question: string) => {
    if (!question.trim() || busy) return;
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setQ("");
    setBusy(true);
    const a = await askPaper(paper, question);
    setMsgs((m) => [...m, { role: "ai", text: a }]);
    setBusy(false);
  };

  return (
    <section className="flex flex-col rounded-2xl border bg-card shadow-soft">
      <div className="border-b p-4">
        <h3 className="text-sm font-bold">Ask AI about this paper</h3>
        <p className="text-xs text-muted-foreground">Answers are based only on this paper's content.</p>
      </div>
      <div className="max-h-96 min-h-40 space-y-3 overflow-y-auto p-4">
        {msgs.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTED.map((s) => (
              <button key={s} onClick={() => ask(s)} className="rounded-full border bg-surface px-3 py-1.5 text-left text-xs font-medium text-muted-foreground transition hover:border-primary/40 hover:text-primary">
                {s}
              </button>
            ))}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={cn("animate-rise whitespace-pre-line text-sm leading-relaxed", m.role === "user" ? "ml-auto w-fit max-w-[85%] rounded-2xl rounded-br-md bg-primary px-3.5 py-2 text-primary-foreground" : "text-foreground")}>
            {m.role === "ai" && <Bot className="mb-1 size-4 text-primary" />}
            {m.text}
          </div>
        ))}
        {busy && <div className="flex items-center gap-2 text-xs text-muted-foreground"><Loader2 className="size-3.5 animate-spin" /> Reading the paper…</div>}
        <div ref={endRef} />
      </div>
      <form onSubmit={(e) => { e.preventDefault(); ask(q); }} className="m-3 flex items-center gap-2 rounded-full border bg-surface p-1.5 pl-4 focus-within:border-primary/40 focus-within:ring-4 focus-within:ring-primary/10">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask a question about this paper..." className="min-w-0 flex-1 bg-transparent text-sm outline-none" />
        <Button type="submit" size="icon" variant="hero" className="size-8" disabled={!q.trim() || busy} aria-label="Send"><Send /></Button>
      </form>
    </section>
  );
}
