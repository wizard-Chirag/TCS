import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search, FileX2, Star } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Container, EmptyState, PageHeader } from "@/components/page-header";
import { PaperCard } from "@/components/paper-card";
import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/history")({
  head: () => ({
    meta: [
      { title: "History — MedBrief AI" },
      { name: "description", content: "Search, filter and sort every medical paper you've summarized." },
      { property: "og:title", content: "History — MedBrief AI" },
      { property: "og:description", content: "Your summarized medical literature, searchable and filterable." },
    ],
  }),
  component: HistoryPage,
});

const DAY = 86_400_000;

function HistoryPage() {
  const papers = useStore((s) => s.papers);
  const collections = useStore((s) => s.collections);
  const [q, setQ] = useState("");
  const [date, setDate] = useState("all");
  const [type, setType] = useState("all");
  const [col, setCol] = useState("all");
  const [sort, setSort] = useState("newest");
  const [favOnly, setFavOnly] = useState(false);

  const list = useMemo(() => {
    const ql = q.toLowerCase();
    const ranges: Record<string, number> = { today: DAY, week: 7 * DAY, month: 30 * DAY };
    return papers
      .filter((p) => !ql || `${p.title} ${p.summary.executive} ${p.tags.join(" ")}`.toLowerCase().includes(ql))
      .filter((p) => date === "all" || Date.now() - p.summarizedAt < (ranges[date] ?? Infinity))
      .filter((p) => type === "all" || p.fileType === type)
      .filter((p) => col === "all" || p.collectionIds.includes(col))
      .filter((p) => !favOnly || p.favorite)
      .sort((a, b) => (sort === "newest" ? b.summarizedAt - a.summarizedAt : a.summarizedAt - b.summarizedAt));
  }, [papers, q, date, type, col, sort, favOnly]);

  return (
    <Container>
      <PageHeader title="History" subtitle={`${papers.length} summaries`} />
      <div className="mb-6 flex flex-col gap-3 rounded-2xl border bg-card p-3 shadow-soft lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search papers, findings, tags..." className="h-10 rounded-xl border-0 bg-muted/60 pl-9 shadow-none" />
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
          <Filter value={date} onChange={setDate} items={[["all", "Any date"], ["today", "Today"], ["week", "Past week"], ["month", "Past month"]]} />
          <Filter value={type} onChange={setType} items={[["all", "All types"], ["pdf", "PDF"], ["image", "Image"], ["text", "Text"], ["docx", "DOCX"]]} />
          <Filter value={col} onChange={setCol} items={[["all", "All collections"], ...collections.map((c) => [c.id, c.name] as [string, string])]} />
          <Filter value={sort} onChange={setSort} items={[["newest", "Newest"], ["oldest", "Oldest"]]} />
          <Button variant="soft" onClick={() => setFavOnly((f) => !f)} className={cn("h-10", favOnly && "border-warning/50 text-warning")}>
            <Star className={cn(favOnly && "fill-warning")} /> Favorites
          </Button>
        </div>
      </div>
      {papers.length === 0 ? (
        <EmptyState icon={<FileX2 />} title="No summaries yet. Upload your first medical paper to get started.">
          <Button asChild variant="hero"><Link to="/new">New summary</Link></Button>
        </EmptyState>
      ) : list.length === 0 ? (
        <EmptyState icon={<Search />} title="No papers match these filters." />
      ) : (
        <div className="grid gap-3">{list.map((p) => <PaperCard key={p.id} paper={p} />)}</div>
      )}
    </Container>
  );
}

function Filter({ value, onChange, items }: { value: string; onChange: (v: string) => void; items: [string, string][] }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="h-10 rounded-full bg-surface sm:w-40"><SelectValue /></SelectTrigger>
      <SelectContent>{items.map(([v, l]) => <SelectItem key={v} value={v}>{l}</SelectItem>)}</SelectContent>
    </Select>
  );
}
