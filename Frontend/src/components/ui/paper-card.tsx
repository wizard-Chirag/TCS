import { Link, useNavigate } from "@tanstack/react-router";
import { Star, MoreHorizontal, ExternalLink, Pencil, Bookmark, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { FileIcon, fileLabel } from "./file-icon";
import { actions } from "@/lib/store";
import { formatDate, timeAgo } from "@/lib/format";
import type { Paper } from "@/lib/types";
import { cn } from "@/lib/utils";

export function FavoriteButton({ paper }: { paper: Paper }) {
  return (
    <button
      aria-label={paper.favorite ? "Remove favorite" : "Add favorite"}
      onClick={(e) => { e.preventDefault(); e.stopPropagation(); actions.toggleFavorite(paper.id); }}
      className="grid size-8 place-items-center rounded-full transition hover:bg-warning/10"
    >
      <Star key={String(paper.favorite)} className={cn("size-4 animate-pop", paper.favorite ? "fill-warning text-warning" : "text-muted-foreground")} />
    </button>
  );
}

export function PaperMenu({ paper }: { paper: Paper }) {
  const navigate = useNavigate();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button onClick={(e) => e.preventDefault()} aria-label="More actions" className="grid size-8 place-items-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground">
          <MoreHorizontal className="size-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
        <DropdownMenuItem onClick={() => navigate({ to: "/paper/$id", params: { id: paper.id } })}><ExternalLink /> Open</DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => {
            const t = window.prompt("Rename paper", paper.title);
            if (t?.trim()) { actions.update(paper.id, { title: t.trim() }); toast.success("Renamed"); }
          }}
        ><Pencil /> Rename</DropdownMenuItem>
        <DropdownMenuItem onClick={() => { actions.toggleSaved(paper.id); toast.success(paper.saved ? "Removed from saved" : "Saved to library"); }}>
          <Bookmark /> {paper.saved ? "Unsave" : "Save"}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => { actions.remove(paper.id); toast("Summary deleted"); }}>
          <Trash2 /> Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function PaperCard({ paper, variant = "list" }: { paper: Paper; variant?: "list" | "grid" }) {
  return (
    <Link
      to="/paper/$id"
      params={{ id: paper.id }}
      className={cn(
        "group relative flex gap-4 rounded-2xl border bg-card p-4 shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/25 hover:shadow-lift sm:p-5",
        variant === "grid" && "flex-col",
      )}
    >
      <FileIcon kind={paper.fileType} />
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1 font-medium text-primary">AI Summary</span>
          <span>· {timeAgo(paper.summarizedAt)}</span>
          {paper.sample && <Badge variant="outline" className="h-5 rounded-full px-2 text-[10px]">Demo</Badge>}
        </div>
        <h3 className="line-clamp-2 font-semibold leading-snug tracking-tight transition-colors group-hover:text-primary">{paper.title}</h3>
        <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-muted-foreground">{paper.summary.executive}</p>
        <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span className="truncate">{paper.authors}</span>
          <span>·</span>
          <span className="truncate italic">{paper.journal}</span>
          <span>·</span>
          <span>{formatDate(paper.published)}</span>
          <span>·</span>
          <span>{fileLabel(paper.fileType)}</span>
        </div>
        {paper.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {paper.tags.map((t) => <span key={t} className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-secondary-foreground">{t}</span>)}
          </div>
        )}
      </div>
      <div className={cn("flex shrink-0 items-start gap-0.5", variant === "grid" && "absolute right-3 top-3")}>
        <FavoriteButton paper={paper} />
        <PaperMenu paper={paper} />
      </div>
    </Link>
  );
}
