import { createFileRoute } from "@tanstack/react-router";
import { ShieldCheck, Layers, FileText } from "lucide-react";
import { Composer } from "@/components/composer";
import { Container } from "@/components/page-header";

export const Route = createFileRoute("/new")({
  head: () => ({
    meta: [
      { title: "New Summary — MedBrief AI" },
      { name: "description", content: "Paste research text or upload a PDF, image or document to generate a structured summary." },
      { property: "og:title", content: "New Summary — MedBrief AI" },
      { property: "og:description", content: "Create a structured AI summary of a medical paper." },
    ],
  }),
  component: NewSummary,
});

function NewSummary() {
  return (
    <Container>
      <div className="mx-auto max-w-3xl pt-6">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">New summary</h1>
        <p className="mt-2 text-muted-foreground">Paste an abstract, or drop a PDF, image or document into the composer.</p>
        <div className="mt-8"><Composer autoFocus /></div>
        <div className="mt-10 grid gap-3 sm:grid-cols-3">
          {[
            { icon: Layers, t: "Structured output", d: "Objective, methods, findings, limitations." },
            { icon: ShieldCheck, t: "Source-grounded", d: "Built only from the text you provide." },
            { icon: FileText, t: "Any format", d: "PDF, image, TXT or DOCX up to 20 MB." },
          ].map(({ icon: I, t, d }) => (
            <div key={t} className="rounded-2xl border bg-card p-4 shadow-soft">
              <I className="mb-2 size-5 text-primary" />
              <div className="text-sm font-semibold">{t}</div>
              <div className="text-xs text-muted-foreground">{d}</div>
            </div>
          ))}
        </div>
      </div>
    </Container>
  );
}
