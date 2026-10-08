import { useRef, useState, type DragEvent } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Paperclip, Image as ImageIcon, FileText, ArrowRight, X, UploadCloud, FileType2, Loader2, Check } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import { FileIcon } from "./file-icon";
import { fileSize } from "@/lib/format";
import { summarize } from "@/lib/mock-ai";
import { actions } from "@/lib/store";
import type { FileKind } from "@/lib/types";
import { cn } from "@/lib/utils";

const STAGES = ["Analyzing document...", "Extracting key findings...", "Generating evidence-grounded summary...", "Finalizing insights..."];

interface Attached {
  file: File;
  kind: FileKind;
  progress: number;
  text?: string;
}

function kindOf(f: File): FileKind {
  if (f.type === "application/pdf" || f.name.endsWith(".pdf")) return "pdf";
  if (f.type.startsWith("image/")) return "image";
  if (f.name.endsWith(".docx")) return "docx";
  return "text";
}

export function Composer({ autoFocus }: { autoFocus?: boolean }) {
  const [text, setText] = useState("");
  const [att, setAtt] = useState<Attached | null>(null);
  const [drag, setDrag] = useState(false);
  const [stage, setStage] = useState<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const open = (accept: string) => {
    if (!inputRef.current) return;
    inputRef.current.accept = accept;
    inputRef.current.click();
  };

  const attach = (file: File) => {
    if (file.size > 20 * 1024 * 1024) { toast.error("File is larger than 20 MB"); return; }
    const kind = kindOf(file);
    const a: Attached = { file, kind, progress: 0 };
    setAtt(a);
    if (kind === "text") file.text().then((t) => setAtt((cur) => (cur ? { ...cur, text: t } : cur)));
    let p = 0;
    const iv = setInterval(() => {
      p += 12 + Math.random() * 18;
      setAtt((cur) => (cur ? { ...cur, progress: Math.min(100, p) } : cur));
      if (p >= 100) clearInterval(iv);
    }, 120);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f) attach(f);
  };

  const canSubmit = (text.trim().length > 0 || (att && att.progress >= 100)) && stage === null;

  const submit = async () => {
    if (!canSubmit) return;
    const body = [att?.text, text].filter(Boolean).join("\n\n");
    const paper = await summarize(
      { text: body, fileName: att?.file.name, fileType: att?.kind ?? "text" },
      setStage,
    );
    actions.addPaper(paper);
    toast.success("Summary ready");
    setStage(null);
    navigate({ to: "/paper/$id", params: { id: paper.id } });
  };

  return (
    <div className="relative">
      <div aria-hidden className="pointer-events-none absolute -inset-x-10 -top-16 h-56 bg-glow blur-2xl" />
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        className={cn(
          "composer-ring relative rounded-3xl shadow-composer transition-all duration-300",
          drag && "scale-[1.01] ring-4 ring-primary/20",
        )}
      >
        {drag && (
          <div className="absolute inset-2 z-10 grid place-items-center rounded-2xl border-2 border-dashed border-primary/50 bg-accent/80 backdrop-blur-sm animate-in fade-in">
            <div className="flex flex-col items-center gap-2 text-accent-foreground">
              <UploadCloud className="size-8 animate-bounce" />
              <span className="font-semibold">Drop your paper here</span>
              <span className="text-xs text-muted-foreground">PDF, image, TXT or DOCX</span>
            </div>
          </div>
        )}

        {stage !== null && (
          <div className="absolute inset-0 z-20 flex flex-col justify-center gap-3 rounded-3xl bg-surface/95 p-6 backdrop-blur animate-in fade-in sm:p-8">
            {STAGES.map((s, i) => (
              <div key={s} className={cn("flex items-center gap-3 text-sm transition-all", i > stage ? "opacity-35" : "opacity-100")}>
                <div className={cn("grid size-6 place-items-center rounded-full", i < stage ? "bg-success/15 text-success" : i === stage ? "bg-primary/10 text-primary" : "bg-muted")}>
                  {i < stage ? <Check className="size-3.5" /> : i === stage ? <Loader2 className="size-3.5 animate-spin" /> : null}
                </div>
                <span className={cn(i === stage && "font-semibold text-foreground")}>{s}</span>
              </div>
            ))}
            <div className="mt-2 space-y-2">
              <div className="h-2.5 w-3/4 rounded-full animate-shimmer" />
              <div className="h-2.5 w-1/2 rounded-full animate-shimmer" />
            </div>
          </div>
        )}

        {att && (
          <div className="mx-4 mt-4 flex items-center gap-3 rounded-2xl border bg-muted/50 p-3 animate-rise">
            <FileIcon kind={att.kind} />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-semibold">{att.file.name}</div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>{fileSize(att.file.size)}</span>
                <span>·</span>
                <span>{att.progress >= 100 ? "Ready" : `Uploading ${Math.round(att.progress)}%`}</span>
              </div>
              {att.progress < 100 && <Progress value={att.progress} className="mt-1.5 h-1" />}
            </div>
            <button onClick={() => setAtt(null)} aria-label="Remove file" className="grid size-8 place-items-center rounded-full text-muted-foreground transition hover:bg-destructive/10 hover:text-destructive">
              <X className="size-4" />
            </button>
          </div>
        )}

        <textarea
          autoFocus={autoFocus}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(); }}
          placeholder="Paste a medical abstract or research text here..."
          rows={5}
          className="block w-full resize-none bg-transparent px-6 pt-5 text-[15px] leading-relaxed outline-none placeholder:text-muted-foreground/70 sm:min-h-[150px]"
        />

        <div className="flex flex-wrap items-center gap-1.5 px-3 pb-3 pt-1 sm:px-4 sm:pb-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="rounded-full text-muted-foreground"><Paperclip /> <span className="hidden sm:inline">Upload</span></Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-52">
              <DropdownMenuItem onClick={() => open(".pdf,application/pdf")}><FileText /> Upload PDF</DropdownMenuItem>
              <DropdownMenuItem onClick={() => open("image/*")}><ImageIcon /> Upload Image</DropdownMenuItem>
              <DropdownMenuItem onClick={() => open(".txt,.docx,text/plain")}><FileType2 /> Upload TXT/DOCX</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant="ghost" size="sm" className="rounded-full text-muted-foreground" onClick={() => open("image/*")}><ImageIcon /> <span className="hidden sm:inline">Image</span></Button>
          <Button variant="ghost" size="sm" className="rounded-full text-muted-foreground" onClick={() => open(".pdf,application/pdf")}><FileText /> <span className="hidden sm:inline">PDF</span></Button>
          <span className="ml-2 hidden text-xs text-muted-foreground lg:inline">or drag & drop</span>
          <Button variant="hero" size="lg" className="ml-auto" disabled={!canSubmit} onClick={submit}>
            Summarize <ArrowRight />
          </Button>
        </div>
        <input ref={inputRef} type="file" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) attach(f); e.target.value = ""; }} />
      </div>
    </div>
  );
}
