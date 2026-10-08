import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { FolderPlus, FolderOpen, Plus, Check } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Container, PageHeader } from "@/components/page-header";
import { actions, useStore } from "@/lib/store";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/collections")({
  head: () => ({
    meta: [
      { title: "Collections — MedBrief AI" },
      { name: "description", content: "Organize saved medical papers into research collections." },
      { property: "og:title", content: "Collections — MedBrief AI" },
      { property: "og:description", content: "Group papers into collections like Cardiology or Oncology." },
    ],
  }),
  component: Collections,
});

function Collections() {
  const collections = useStore((s) => s.collections);
  const papers = useStore((s) => s.papers);
  const [name, setName] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string | null>(null);

  const create = () => {
    if (!name.trim()) return;
    actions.addCollection(name.trim());
    toast.success(`Collection "${name.trim()}" created`);
    setName("");
    setOpen(false);
  };

  return (
    <Container>
      <PageHeader
        title="Collections"
        subtitle="Group related research for faster review."
        actions={
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild><Button variant="hero"><FolderPlus /> New collection</Button></DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>New collection</DialogTitle></DialogHeader>
              <form onSubmit={(e) => { e.preventDefault(); create(); }} className="flex gap-2">
                <Input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Neurology" />
                <Button type="submit" variant="hero">Create</Button>
              </form>
            </DialogContent>
          </Dialog>
        }
      />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {collections.map((c) => {
          const items = papers.filter((p) => p.collectionIds.includes(c.id));
          return (
            <button
              key={c.id}
              onClick={() => setActive(active === c.id ? null : c.id)}
              className={cn("group rounded-2xl border bg-card p-5 text-left shadow-soft transition-all hover:-translate-y-0.5 hover:shadow-lift", active === c.id && "border-primary ring-4 ring-primary/10")}
            >
              <div className="mb-4 grid size-11 place-items-center rounded-xl" style={{ background: `oklch(0.95 0.04 ${c.hue})`, color: `oklch(0.5 0.15 ${c.hue})` }}>
                <FolderOpen className="size-5" />
              </div>
              <div className="font-semibold">{c.name}</div>
              <div className="text-xs text-muted-foreground">{c.description}</div>
              <div className="mt-3 text-xs font-semibold text-primary">{items.length} papers</div>
            </button>
          );
        })}
      </div>

      {active && (
        <section className="mt-8 animate-rise rounded-2xl border bg-card p-5 shadow-soft">
          <h2 className="mb-1 font-bold">{collections.find((c) => c.id === active)?.name}</h2>
          <p className="mb-4 text-sm text-muted-foreground">Add or remove saved papers.</p>
          <div className="divide-y">
            {papers.map((p) => {
              const inC = p.collectionIds.includes(active);
              return (
                <div key={p.id} className="flex items-center gap-3 py-3">
                  <Link to="/paper/$id" params={{ id: p.id }} className="min-w-0 flex-1 truncate text-sm font-medium hover:text-primary">{p.title}</Link>
                  <Button size="sm" variant={inC ? "secondary" : "soft"} className="rounded-full" onClick={() => actions.toggleInCollection(p.id, active)}>
                    {inC ? <><Check /> Added</> : <><Plus /> Add</>}
                  </Button>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </Container>
  );
}
