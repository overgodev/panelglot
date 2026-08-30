export type StatusKey =
  | "upload"
  | "pending"
  | "detection"
  | "ocr"
  | "textline_merge"
  | "mask-generation"
  | "inpainting"
  | "upscaling"
  | "translating"
  | "rendering"
  | "finished"
  | "error"
  | "error-upload"
  | "error-lang"
  | "error-translating"
  | "error-too-large"
  | "error-disconnect"
  | null;

export interface ChunkProcessingResult {
  updatedBuffer: Uint8Array;
}

/** [x1,y1,x2,y2,x3,y3,x4,y4] - four corners, in ORIGINAL (pre-upscale) image pixel
 * coordinates. Matches manga_translator/config.py DetectorConfig.manual_text_boxes. */
export type ManualBox = number[];

export interface OcrPreviewRegion {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  text: string;
}

export const processingStatuses = [
  "upload",
  "pending",
  "detection",
  "ocr",
  "textline_merge",
  "mask-generation",
  "inpainting",
  "upscaling",
  "translating",
  "rendering",
];

// Kept in sync with manga_translator/config.py's `Translator` enum, which
// only has these three since the non-LM-Studio backends were removed
// (see docs/HANDOFF.md "Translator backend cleanup").
export type TranslatorKey = "custom_openai" | "original" | "none";

export const validTranslators: TranslatorKey[] = ["custom_openai", "original", "none"];

export type LlmServerType = "ollama" | "openai-compatible" | "unknown";

export interface CustomEndpoint {
  id: string;
  name: string;
  baseUrl: string;
  model: string;
  apiKey: string;
  serverType: LlmServerType;
  verified: boolean;
  lastUsedAt: string | null;
}

export interface UploadedFile {
  id: string;
  file: File;
}

export interface FileStatus {
  status: StatusKey | null;
  progress: string | null;
  queuePos: string | null;
  result: Blob | null;
  error: string | null;
}

export interface TranslationSettings {
  detectionResolution: string;
  textDetector: string;
  renderTextDirection: string;
  translator: TranslatorKey;
  targetLanguage: string;
  inpaintingSize: string;
  customUnclipRatio: number;
  customBoxThreshold: number;
  maskDilationOffset: number;
  inpainter: string;
  colorizer: string;
  ocr: string;
}

export interface StoryContext {
  projectName: string;
  glossary: string;
}

export interface FinishedImage {
  id: string;
  originalName: string;
  result: Blob;
  finishedAt: Date;
  settings: TranslationSettings;
}

export interface StoryPage {
  id: string;
  originalName: string;
  imageDataUrl: string;
  resultDataUrl: string | null;
}

export interface SavedStory {
  id: string;
  name: string;
  createdAt: string;
  settings: TranslationSettings;
  storyContext: StoryContext;
  pages: StoryPage[];
}
