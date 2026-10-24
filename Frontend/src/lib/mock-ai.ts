/**
 * Mock AI layer. Replace these functions with real API calls later
 * (e.g. a server function calling the AI gateway). Output is derived
 * only from the provided text — nothing is invented beyond it.
 */
import type { FileKind, Paper } from "./types";

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

function sentences(text: string) {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+(?=[A-Z0-9])/)
    .map((s) => s.trim())
    .filter((s) => s.length > 20);
}

function pick(list: string[], re: RegExp, fallback = "Not clearly reported in the provided text.") {
  return list.find((s) => re.test(s)) ?? fallback;
}

export interface SummarizeInput {
  text: string;
  fileName?: string | undefined;
  fileType: FileKind;
}

export async function summarize(input: SummarizeInput, onStage?: (i: number) => void): Promise<Paper> {
  for (let i = 0; i < 4; i++) {
    onStage?.(i);
    await wait(900);
  }
  const text = input.text.trim();
  const s = sentences(text);
  const firstLine = text.split("\n")[0]?.trim() ?? "";
  const title =
    firstLine && firstLine.length < 160 && !/[.!?]$/.test(firstLine)
      ? firstLine
      : input.fileName?.replace(/\.[^.]+$/, "").replace(/[_-]+/g, " ") || "Untitled research text";
  const numeric = s.filter((x) => /\d/.test(x) && /(%|CI|HR|OR|RR|p\s*[<=]|reduc|increas|associated)/i.test(x));
  const limits = s.filter((x) => /(limit|bias|confound|small sample|retrospective|caution)/i.test(x));
  const has = s.length > 0;

  return {
    id: `p-${Date.now()}`,
    title,
    authors: "Not specified",
    journal: input.fileName ? "Uploaded document" : "Pasted text",
    published: "—",
    fileType: input.fileType,
    fileName: input.fileName,
    summarizedAt: Date.now(),
    favorite: false,
    saved: false,
    collectionIds: [],
    tags: [],
    sample: false,
    sourceText: text,
    summary: {
      executive: has
        ? s.slice(0, 3).join(" ")
        : "The uploaded file could not be read as text in this demo. Connect the AI backend to extract content from PDFs and images.",
      objective: pick(s, /(aim|objective|purpose|we sought|to (determine|evaluate|assess|investigate))/i),
      methodology: [
        { label: "Study design", value: pick(s, /(randomi[sz]ed|cohort|meta-analysis|cross-sectional|case-control|trial|review)/i) },
        { label: "Population", value: pick(s, /(patients|participants|adults|children|subjects|women|men)/i) },
        { label: "Sample size", value: (text.match(/\b\d[\d,]{1,}\s+(patients|participants|subjects|adults)/i)?.[0]) ?? "Not reported" },
      ],
      findings: numeric.length ? numeric.slice(0, 5) : s.slice(3, 6),
      conclusion: pick(s, /(conclu|suggest|indicate|in summary)/i, s[s.length - 1] ?? "Not reported."),
      clinical:
        "Clinical relevance should be judged against the full publication and current guidelines. This demo extracts statements from your text and does not provide medical advice.",
      limitations: limits.length ? limits.slice(0, 3) : ["No limitations were explicitly stated in the provided text."],
      takeaways: (numeric.length ? numeric : s).slice(0, 3).map((x) => (x.length > 90 ? x.slice(0, 87) + "…" : x)),
    },
    compare: {
      design: pick(s, /(randomi[sz]ed|cohort|meta-analysis|trial|review)/i, "—"),
      population: pick(s, /(patients|participants|adults)/i, "—"),
      sampleSize: "—",
      intervention: "—",
      outcome: "—",
    },
  };
}

export async function askPaper(paper: Paper, question: string): Promise<string> {
  await wait(900);
  const q = question.toLowerCase();
  const s = paper.summary;
  if (/limit/.test(q)) return "The paper notes these limitations:\n• " + s.limitations.join("\n• ");
  if (/population|participant|who/.test(q))
    return s.methodology.filter((m) => /population|sample/i.test(m.label)).map((m) => `${m.label}: ${m.value}`).join("\n");
  if (/find|result/.test(q)) return "Key findings reported:\n• " + s.findings.join("\n• ");
  if (/simple|plain|explain/.test(q)) return `In plain terms: ${s.conclusion} ${s.takeaways[0] ? `The headline: ${s.takeaways[0].toLowerCase()}.` : ""}`;
  if (/compar|previous|other/.test(q))
    return "This document doesn't include enough information to compare with prior research. Add related papers in Compare Papers to analyze them side by side.";
  if (/method|design/.test(q)) return s.methodology.map((m) => `${m.label}: ${m.value}`).join("\n");
  return `Based only on this paper: ${s.executive}`;
}
