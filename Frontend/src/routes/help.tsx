import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import { Container, PageHeader } from "@/components/page-header";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/help")({
  head: () => ({
    meta: [
      { title: "Help & Feedback — MedBrief AI" },
      { name: "description", content: "Answers to common questions and a way to send feedback." },
      { property: "og:title", content: "Help & Feedback — MedBrief AI" },
      { property: "og:description", content: "Get help with MedBrief AI." },
    ],
  }),
  component: Help,
});

const faq: [string, string][] = [
  ["What can I upload?", "PDF, images, TXT and DOCX files up to 20 MB, or paste text directly."],
  ["Is the summary accurate?", "Summaries are generated from your source only. Always verify important findings against the original publication."],
  ["Is this medical advice?", "No. MedBrief AI summarizes research and does not provide personalized medical advice."],
];

function Help() {
  return (
    <Container>
      <div className="mx-auto max-w-2xl">
        <PageHeader title="Help & Feedback" />
        <Accordion type="single" collapsible className="rounded-2xl border bg-card px-5 shadow-soft">
          {faq.map(([q, a]) => (
            <AccordionItem key={q} value={q}><AccordionTrigger>{q}</AccordionTrigger><AccordionContent className="text-muted-foreground">{a}</AccordionContent></AccordionItem>
          ))}
        </Accordion>
        <form onSubmit={(e) => { e.preventDefault(); toast.success("Thanks for your feedback!"); (e.target as HTMLFormElement).reset(); }} className="mt-6 space-y-3 rounded-2xl border bg-card p-5 shadow-soft">
          <h2 className="font-semibold">Send feedback</h2>
          <Textarea required placeholder="Tell us what would make MedBrief AI better…" rows={4} />
          <Button type="submit" variant="hero">Send</Button>
        </form>
      </div>
    </Container>
  );
}
