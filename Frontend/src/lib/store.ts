import { useSyncExternalStore } from "react";
import { demoCollections, demoPapers } from "./demo-data";
import type { Collection, Paper } from "./types";

interface State {
  papers: Paper[];
  collections: Collection[];
}

const KEY = "medbrief-state-v1";
let state: State = { papers: demoPapers, collections: demoCollections };
let hydrated = false;
const listeners = new Set<() => void>();

function hydrate() {
  if (hydrated || typeof window === "undefined") return;
  hydrated = true;
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) state = JSON.parse(raw);
  } catch {
    /* ignore */
  }
}

function set(next: Partial<State>) {
  state = { ...state, ...next };
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* ignore */
  }
  listeners.forEach((l) => l());
}

const serverSnapshot: State = { papers: demoPapers, collections: demoCollections };

export function useStore<T>(selector: (s: State) => T): T {
  return useSyncExternalStore(
    (l) => {
      listeners.add(l);
      if (!hydrated) {
        hydrate();
        queueMicrotask(() => listeners.forEach((x) => x()));
      }
      return () => listeners.delete(l);
    },
    () => selector(state),
    () => selector(serverSnapshot),
  );
}

export const actions = {
  addPaper(p: Paper) {
    set({ papers: [p, ...state.papers] });
  },
  update(id: string, patch: Partial<Paper>) {
    set({ papers: state.papers.map((p) => (p.id === id ? { ...p, ...patch } : p)) });
  },
  toggleFavorite(id: string) {
    const p = state.papers.find((x) => x.id === id);
    if (p) actions.update(id, { favorite: !p.favorite });
  },
  toggleSaved(id: string) {
    const p = state.papers.find((x) => x.id === id);
    if (p) actions.update(id, { saved: !p.saved });
  },
  remove(id: string) {
    set({ papers: state.papers.filter((p) => p.id !== id) });
  },
  addCollection(name: string) {
    const c: Collection = {
      id: `c-${Date.now()}`,
      name,
      description: "Custom collection",
      hue: Math.floor(Math.random() * 360),
    };
    set({ collections: [...state.collections, c] });
    return c;
  },
  toggleInCollection(paperId: string, collectionId: string) {
    const p = state.papers.find((x) => x.id === paperId);
    if (!p) return;
    const has = p.collectionIds.includes(collectionId);
    actions.update(paperId, {
      collectionIds: has ? p.collectionIds.filter((c) => c !== collectionId) : [...p.collectionIds, collectionId],
    });
  },
  reset() {
    set({ papers: demoPapers, collections: demoCollections });
  },
};
