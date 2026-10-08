import { FileText, Image as ImageIcon, FileType2, File } from "lucide-react";
import type { FileKind } from "@/lib/types";
import { cn } from "@/lib/utils";

const map = {
  pdf: { icon: FileText, label: "PDF", cls: "bg-destructive/10 text-destructive" },
  image: { icon: ImageIcon, label: "Image", cls: "bg-teal/10 text-teal" },
  docx: { icon: FileType2, label: "DOCX", cls: "bg-primary/10 text-primary" },
  text: { icon: File, label: "Text", cls: "bg-muted text-muted-foreground" },
} as const;

export function FileIcon({ kind, className }: { kind: FileKind; className?: string }) {
  const m = map[kind];
  const Icon = m.icon;
  return (
    <div className={cn("grid size-10 shrink-0 place-items-center rounded-lg", m.cls, className)}>
      <Icon className="size-5" />
    </div>
  );
}

export const fileLabel = (k: FileKind) => map[k].label;
