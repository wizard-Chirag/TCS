import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search, LayoutGrid, List, Bookmark, Star } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Container, EmptyState, PageHeader } from "@/components/page-header";
import { PaperCard } from "@/components/paper-card";
import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/saved")({
  head: () => ({
    meta: [
      { title: "Saved Papers — MedBrief AI" },
      { name: "description", content: "Your bookmarked medical research, organized by tags and collections." },
      { property: "og:title", content: "Saved Papers — MedBrief AI" },
      { property: "og:description", content: "Bookmarked medical research library." },
    ],
  }),
  component: Saved,
});

function Saved() {
  const papers = useStore((s) => s.papers.filter((p) => p.saved));
  const collections = useStore((s) => s.collections);
  const [view, setView] = useState("grid");
  const [q, setQ] = useState("");
  const [tag, setTag] = useState<string | null>(null);
  const [col, setCol] = useState<string | null>(null);
  const [fav, setFav] = useState(false);
  const tags = useMemo(() => [...new Set(papers.flatMap((p) => p.tags))], [papers]);

  const list = papers
    .filter((p) => !q || p.title.toLowerCase().includes(q.toLowerCase()))
    .filter((p) => !tag || p.tags.includes(tag))
    .filter((p) => !col || p.collectionIds.includes(col))
    .filter((p) => !fav || p.favorite);

  const Chip = ({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) => (
    <button onClick={onClick} className={cn("rounded-full border px-3 py-1 text-xs font-medium transition", active ? "border-primary bg-primary text-primary-foreground" : "bg-surface text-muted-foreground hover:border-primary/40 hover:text-primary")}>{children}</button>
  );

  return (
    <Container>
      <PageHeader
        title="Saved Papers"
        subtitle="Your bookmarked research library."
        actions={
          <ToggleGroup type="single" value={view} onValueChange={(v) => v && setView(v)} className="rounded-full border bg-surface p-1">
            <ToggleGroupItem value="grid" aria-label="Grid view" className="rounded-full"><LayoutGrid className="size-4" /></ToggleGroupItem>
            <ToggleGroupItem value="list" aria-label="List view" className="rounded-full"><List className="size-4" /></ToggleGroupItem>
          </ToggleGroup>
        }
      />
      <div className="mb-6 space-y-3">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search saved papers" className="h-10 rounded-full bg-surface pl-9" />
        </div>
        <div className="flex flex-wrap gap-2">
          <Chip active={fav} onClick={() => setFav(!fav)}><Star className="mr-1 inline size-3" />Favorites</Chip>
          {collections.map((c) => <Chip key={c.id} active={col === c.id} onClick={() => setCol(col === c.id ? null : c.id)}>{c.name}</Chip>)}
          {tags.map((t) => <Chip key={t} active={tag === t} onClick={() => setTag(tag === t ? null : t)}>#{t}</Chip>)}
        </div>
      </div>
      {list.length === 0 ? (
        <EmptyState icon={<Bookmark />} title="No saved papers yet. Save a summary to keep it here.">
          <Button asChild variant="hero"><Link to="/history">Browse history</Link></Button>
        </EmptyState>
      ) : (
        <div className={cn("grid gap-3", view === "grid" && "sm:grid-cols-2 xl:grid-cols-3")}>
          {list.map((p) => <PaperCard key={p.id} paper={p} variant={view === "grid" ? "grid" : "list"} />)}
        </div>
      )}
    </Container>
  );
}
