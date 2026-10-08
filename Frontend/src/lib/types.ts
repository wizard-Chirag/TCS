export type FileKind = "pdf" | "image" | "text" | "docx";

export interface PaperSummary {
  executive: string;
  objective: string;
  methodology: { label: string; value: string }[];
  findings: string[];
  conclusion: string;
  clinical: string;
  limitations: string[];
  takeaways: string[];
}

export interface Paper {
  id: string;
  title: string;
  authors: string;
  journal: string;
  published: string;
  doi?: string;
  pmid?: string;
  fileType: FileKind;
  fileName?: string | undefined;
  summarizedAt: number;
  favorite: boolean;
  saved: boolean;
  collectionIds: string[];
  tags: string[];
  sample: boolean;
  sourceText?: string;
  summary: PaperSummary;
  compare: {
    design: string;
    population: string;
    sampleSize: string;
    intervention: string;
    outcome: string;
  };
}

export interface Collection {
  id: string;
  name: string;
  description: string;
  hue: number;
}
