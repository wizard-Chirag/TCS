import { Link, useRouterState } from "@tanstack/react-router";
import {
  Home, PlusCircle, History, Bookmark, FolderOpen, GitCompareArrows, Settings, LifeBuoy,
  PanelLeftClose, PanelLeftOpen, Clock, Star, Menu, Bell, Search,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";
import { Logo } from "./logo";
import { useStore } from "@/lib/store";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const nav = [
  { to: "/", label: "Home", icon: Home },
  { to: "/new", label: "New Summary", icon: PlusCircle },
  { to: "/history", label: "History", icon: History },
  { to: "/saved", label: "Saved Papers", icon: Bookmark },
  { to: "/collections", label: "Collections", icon: FolderOpen },
  { to: "/compare", label: "Compare Papers", icon: GitCompareArrows },
] as const;

function SidebarBody({ collapsed, onNavigate }: { collapsed: boolean; onNavigate?: () => void }) {
  const path = useRouterState({ select: (s) => s.location.pathname });
  const papers = useStore((s) => s.papers);
  const collections = useStore((s) => s.collections);
  const recent = papers.slice(0, 3);
  const favs = papers.filter((p) => p.favorite).slice(0, 3);

  const Item = ({ to, label, icon: Icon }: { to: string; label: string; icon: typeof Home }) => {
    const active = to === "/" ? path === "/" : path.startsWith(to);
    const link = (
      <Link
        to={to}
        onClick={onNavigate}
        className={cn(
          "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all",
          active
            ? "bg-surface text-sidebar-accent-foreground shadow-soft"
            : "text-sidebar-foreground/75 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
          collapsed && "justify-center px-0",
        )}
      >
        <Icon className={cn("size-[18px] shrink-0", active && "text-primary")} />
        {!collapsed && <span className="truncate">{label}</span>}
      </Link>
    );
    if (!collapsed) return link;
    return (
      <Tooltip>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent side="right">{label}</TooltipContent>
      </Tooltip>
    );
  };

  const Mini = ({ title, icon: Icon, items }: { title: string; icon: typeof Home; items: { id: string; name: string; to: string }[] }) =>
    collapsed ? null : (
      <div className="mt-5">
        <div className="mb-1.5 flex items-center gap-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          <Icon className="size-3.5" /> {title}
        </div>
        {items.map((i) => (
          <Link
            key={i.id}
            to={i.to}
            onClick={onNavigate}
            className="block truncate rounded-md px-3 py-1.5 text-[13px] text-sidebar-foreground/70 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          >
            {i.name}
          </Link>
        ))}
      </div>
    );

  return (
    <div className="flex h-full flex-col">
      <div className={cn("flex h-16 items-center gap-2.5 px-4", collapsed && "justify-center px-0")}>
        <Logo />
        {!collapsed && <span className="text-[15px] font-bold tracking-tight">MedBrief <span className="text-brand">AI</span></span>}
      </div>
      <div className="flex-1 overflow-y-auto px-3 pb-4">
        <nav className="space-y-0.5">{nav.map((n) => <Item key={n.to} {...n} />)}</nav>
        <Mini title="Recent Papers" icon={Clock} items={recent.map((p) => ({ id: p.id, name: p.title, to: `/paper/${p.id}` }))} />
        <Mini title="Favorites" icon={Star} items={favs.map((p) => ({ id: p.id, name: p.title, to: `/paper/${p.id}` }))} />
        <Mini title="My Collections" icon={FolderOpen} items={collections.map((c) => ({ id: c.id, name: c.name, to: "/collections" }))} />
      </div>
      <div className="space-y-0.5 border-t border-sidebar-border p-3">
        <Item to="/settings" label="Settings" icon={Settings} />
        <Item to="/help" label="Help & Feedback" icon={LifeBuoy} />
        <div className={cn("mt-2 flex items-center gap-3 rounded-lg p-2", collapsed && "justify-center")}>
          <Avatar />
          {!collapsed && (
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold">Dr. Alex Morgan</div>
              <div className="truncate text-xs text-muted-foreground">Researcher · Demo</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function Avatar({ className }: { className?: string }) {
  return (
    <div className={cn("grid size-8 shrink-0 place-items-center rounded-full bg-brand text-xs font-bold text-primary-foreground ring-2 ring-surface", className)}>
      AM
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const path = useRouterState({ select: (s) => s.location.pathname });

  return (
    <TooltipProvider delayDuration={150}>
      <div className="flex min-h-screen">
        <aside
          className={cn(
            "sticky top-0 hidden h-screen shrink-0 border-r border-sidebar-border bg-sidebar transition-[width] duration-300 md:block",
            collapsed ? "w-[68px]" : "w-64",
          )}
        >
          <SidebarBody collapsed={collapsed} />
          <button
            onClick={() => setCollapsed((c) => !c)}
            aria-label="Toggle sidebar"
            className="absolute -right-3 top-5 grid size-6 place-items-center rounded-full border bg-surface text-muted-foreground shadow-soft transition hover:text-primary"
          >
            {collapsed ? <PanelLeftOpen className="size-3.5" /> : <PanelLeftClose className="size-3.5" />}
          </button>
        </aside>

        <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
          <SheetContent side="left" className="w-72 bg-sidebar p-0">
            <SheetTitle className="sr-only">Navigation</SheetTitle>
            <SidebarBody collapsed={false} onNavigate={() => setMobileOpen(false)} />
          </SheetContent>
        </Sheet>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border/60 bg-background/80 px-4 backdrop-blur-xl md:px-8">
            <button className="md:hidden" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <Menu className="size-5" />
            </button>
            <div className="flex items-center gap-2 md:hidden">
              <Logo small />
              <span className="font-bold">MedBrief AI</span>
            </div>
            <div className="ml-auto flex items-center gap-2">
              <Link to="/history" className="hidden items-center gap-2 rounded-full border bg-surface px-3 py-1.5 text-sm text-muted-foreground transition hover:border-primary/40 sm:flex">
                <Search className="size-4" /> Search papers
              </Link>
              <button className="relative grid size-9 place-items-center rounded-full text-muted-foreground transition hover:bg-accent hover:text-accent-foreground" aria-label="Notifications">
                <Bell className="size-[18px]" />
                <span className="absolute right-2 top-2 size-2 rounded-full bg-primary ring-2 ring-background" />
              </button>
              <Avatar />
            </div>
          </header>
          <main key={path} className="flex-1 animate-rise pb-24 md:pb-10">{children}</main>
        </div>

        <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t bg-surface/95 backdrop-blur md:hidden">
          {[nav[0], nav[1], nav[2], nav[3], nav[5]].map(({ to, label, icon: Icon }) => {
            const active = to === "/" ? path === "/" : path.startsWith(to);
            return (
              <Link key={to} to={to} className={cn("flex flex-col items-center gap-0.5 py-2 text-[10px] font-medium", active ? "text-primary" : "text-muted-foreground")}>
                <Icon className="size-5" />
                {label.split(" ")[0]}
              </Link>
            );
          })}
        </nav>
      </div>
    </TooltipProvider>
  );
}
