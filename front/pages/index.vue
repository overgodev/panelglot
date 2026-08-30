<script setup lang="ts">
import {
  processingStatuses,
  type StatusKey,
  type TranslatorKey,
  type FileStatus,
  type TranslationSettings,
  type FinishedImage,
  type UploadedFile,
  type CustomEndpoint,
  type SavedStory,
  type ManualBox,
  type OcrPreviewRegion,
  validTranslators,
} from "~/types";
import { imageMimeTypes } from "~/config";
import { blobToDataUrl, dataUrlToFile, dataUrlToBlob } from "~/utils/blob";
import type { Ref } from "vue";

// State
const files = ref<UploadedFile[]>([]);
const fileStatuses = ref<Map<string, FileStatus>>(new Map());
const finishedImages = ref<FinishedImage[]>([]);
const currentId = ref<string | null>(null);
const tool = ref<"pointer" | "pan" | "lasso">("pointer");
const zoom = ref(1);
const fileInputRef = ref<HTMLInputElement | null>(null);
const rightDockRef = ref<{ markEndpointVerified: () => void } | null>(null);
const showSaveStoryDialog = ref(false);
const manualBoxes = ref<Map<string, ManualBox[]>>(new Map());
const previewRegions = ref<Map<string, OcrPreviewRegion[]>>(new Map());
const pageOverrides = ref<Map<string, Partial<TranslationSettings>>>(new Map());
const isPreviewingOcr = ref(false);

// Translation options
const detectionResolution = ref("1536");
const textDetector = ref("default");
const renderTextDirection = ref("auto");
const translator = ref<TranslatorKey>("custom_openai");
const targetLanguage = ref("CHS");
const endpoint = ref<CustomEndpoint | null>(null);

const inpaintingSize = ref("2048");
const customUnclipRatio = ref(2.3);
const customBoxThreshold = ref(0.7);
const maskDilationOffset = ref(30);
const inpainter = ref("default");
const colorizer = ref("none");
const ocr = ref("48px");

const projectName = ref("");
const glossary = ref("");

// Computed
const isProcessing = computed(() => {
  if (files.value.length === 0 || fileStatuses.value.size === 0) return false;
  return Array.from(fileStatuses.value.values()).some((status) => {
    if (!status || status.status === null) return false;
    return processingStatuses.includes(status.status);
  });
});

const isProcessingAllFinished = computed(() => {
  if (files.value.length === 0 || fileStatuses.value.size === 0) return false;
  return Array.from(fileStatuses.value.values()).every((status) => {
    if (!status || status.status === null) return false;
    return status.status === "finished";
  });
});

const currentIndex = computed(() => files.value.findIndex((f) => f.id === currentId.value));
const currentFile = computed(() => files.value.find((f) => f.id === currentId.value) ?? null);
const currentStatus = computed(() => (currentId.value ? fileStatuses.value.get(currentId.value) ?? null : null));

const currentSettings = (): TranslationSettings => ({
  detectionResolution: detectionResolution.value,
  textDetector: textDetector.value,
  renderTextDirection: renderTextDirection.value,
  translator: translator.value,
  targetLanguage: targetLanguage.value,
  inpaintingSize: inpaintingSize.value,
  customUnclipRatio: customUnclipRatio.value,
  customBoxThreshold: customBoxThreshold.value,
  maskDilationOffset: maskDilationOffset.value,
  inpainter: inpainter.value,
  colorizer: colorizer.value,
  ocr: ocr.value,
});

// Per-page settings overrides: each page can carry its own partial settings on top of the
// global defaults above (see RightDock's "Custom settings for this page" toggle). The raw
// refs (detectionResolution etc.) stay the persisted global defaults; these *Field proxies
// are what the UI actually binds to, transparently reading/writing the current page's
// override when one is enabled.
const pageOverrideEnabled = computed<boolean>({
  get: () => currentId.value !== null && pageOverrides.value.has(currentId.value),
  set: (enabled) => {
    if (!currentId.value) return;
    const next = new Map(pageOverrides.value);
    if (enabled) next.set(currentId.value, {});
    else next.delete(currentId.value);
    pageOverrides.value = next;
  },
});

const resolvedSettingsFor = (pageId: string | null): TranslationSettings => {
  const base = currentSettings();
  if (!pageId) return base;
  const override = pageOverrides.value.get(pageId);
  return override ? { ...base, ...override } : base;
};

const fieldProxy = <K extends keyof TranslationSettings>(key: K, globalRef: Ref<TranslationSettings[K]>) =>
  computed<TranslationSettings[K]>({
    get() {
      if (currentId.value) {
        const override = pageOverrides.value.get(currentId.value);
        if (override && key in override) return override[key] as TranslationSettings[K];
      }
      return globalRef.value;
    },
    set(value) {
      if (currentId.value && pageOverrides.value.has(currentId.value)) {
        const next = new Map(pageOverrides.value);
        next.set(currentId.value, { ...next.get(currentId.value), [key]: value });
        pageOverrides.value = next;
      } else {
        globalRef.value = value;
      }
    },
  });

const detectionResolutionField = fieldProxy("detectionResolution", detectionResolution);
const textDetectorField = fieldProxy("textDetector", textDetector);
const renderTextDirectionField = fieldProxy("renderTextDirection", renderTextDirection);
const translatorField = fieldProxy("translator", translator);
const targetLanguageField = fieldProxy("targetLanguage", targetLanguage);
const inpaintingSizeField = fieldProxy("inpaintingSize", inpaintingSize);
const customUnclipRatioField = fieldProxy("customUnclipRatio", customUnclipRatio);
const customBoxThresholdField = fieldProxy("customBoxThreshold", customBoxThreshold);
const maskDilationOffsetField = fieldProxy("maskDilationOffset", maskDilationOffset);
const inpainterField = fieldProxy("inpainter", inpainter);
const colorizerField = fieldProxy("colorizer", colorizer);
const ocrField = fieldProxy("ocr", ocr);

const applySettings = (settings: TranslationSettings) => {
  detectionResolution.value = settings.detectionResolution;
  textDetector.value = settings.textDetector;
  renderTextDirection.value = settings.renderTextDirection;
  if ((validTranslators as string[]).includes(settings.translator)) translator.value = settings.translator;
  targetLanguage.value = settings.targetLanguage;
  inpaintingSize.value = settings.inpaintingSize;
  customUnclipRatio.value = settings.customUnclipRatio;
  customBoxThreshold.value = settings.customBoxThreshold;
  maskDilationOffset.value = settings.maskDilationOffset;
  inpainter.value = settings.inpainter;
  colorizer.value = settings.colorizer;
  ocr.value = settings.ocr;
};

const hydrateStory = (story: SavedStory) => {
  const restoredFiles: UploadedFile[] = [];
  const restoredStatuses = new Map<string, FileStatus>();
  for (const page of story.pages) {
    const file = dataUrlToFile(page.imageDataUrl, page.originalName);
    restoredFiles.push({ id: page.id, file });
    restoredStatuses.set(page.id, {
      status: page.resultDataUrl ? "finished" : null,
      progress: null,
      queuePos: null,
      result: page.resultDataUrl ? dataUrlToBlob(page.resultDataUrl) : null,
      error: null,
    });
  }
  files.value = restoredFiles;
  fileStatuses.value = restoredStatuses;
  currentId.value = restoredFiles[0]?.id ?? null;
  applySettings(story.settings);
  projectName.value = story.storyContext.projectName;
  glossary.value = story.storyContext.glossary;
};

// Load saved settings / gallery, wire up paste handling
onMounted(() => {
  const saved = loadSettings();
  if (saved.detectionResolution) detectionResolution.value = saved.detectionResolution;
  if (saved.textDetector) textDetector.value = saved.textDetector;
  if (saved.renderTextDirection) renderTextDirection.value = saved.renderTextDirection;
  if (saved.translator && (validTranslators as string[]).includes(saved.translator)) {
    translator.value = saved.translator;
  }
  if (saved.targetLanguage) targetLanguage.value = saved.targetLanguage;
  if (saved.inpaintingSize) inpaintingSize.value = saved.inpaintingSize;
  if (saved.customUnclipRatio) customUnclipRatio.value = saved.customUnclipRatio;
  if (saved.customBoxThreshold) customBoxThreshold.value = saved.customBoxThreshold;
  if (saved.maskDilationOffset) maskDilationOffset.value = saved.maskDilationOffset;
  if (saved.inpainter) inpainter.value = saved.inpainter;
  if (saved.colorizer) colorizer.value = saved.colorizer;
  if (saved.ocr) ocr.value = saved.ocr;

  const savedStory = loadStoryContext();
  if (savedStory.projectName) projectName.value = savedStory.projectName;
  if (savedStory.glossary) glossary.value = savedStory.glossary;

  finishedImages.value = loadFinishedImages();

  const route = useRoute();
  const openStoryId = route.query.openStory;
  if (typeof openStoryId === "string") {
    const story = loadStories().find((s) => s.id === openStoryId);
    if (story) hydrateStory(story);
    navigateTo({ path: "/" }, { replace: true });
  }

  window.addEventListener("paste", handlePaste);
});

onBeforeUnmount(() => {
  window.removeEventListener("paste", handlePaste);
});

watch(
  [
    detectionResolution,
    textDetector,
    renderTextDirection,
    translator,
    targetLanguage,
    inpaintingSize,
    customUnclipRatio,
    customBoxThreshold,
    maskDilationOffset,
    inpainter,
    colorizer,
    ocr,
  ],
  () => saveSettings(currentSettings())
);

watch([projectName, glossary], () => saveStoryContext({ projectName: projectName.value, glossary: glossary.value }));

// File handling
const toUploadedFiles = (rawFiles: File[]): UploadedFile[] =>
  rawFiles.map((file) => ({
    id: `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    file,
  }));

const addFiles = (newFiles: UploadedFile[]) => {
  if (newFiles.length === 0) return;
  files.value = [...files.value, ...newFiles];
  currentId.value = newFiles[0].id;
};

const handlePaste = (e: ClipboardEvent) => {
  const items = e.clipboardData?.items || [];
  for (const item of items) {
    if (item.kind === "file") {
      const pastedFile = item.getAsFile();
      if (pastedFile && imageMimeTypes.includes(pastedFile.type)) {
        addFiles(toUploadedFiles([pastedFile]));
        break;
      }
    }
  }
};

const handleDrop = (e: DragEvent) => {
  const droppedFiles = Array.from(e.dataTransfer?.files || []);
  const validFiles = droppedFiles.filter((file) => imageMimeTypes.includes(file.type));
  addFiles(toUploadedFiles(validFiles));
};

const handleFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const selectedFiles = Array.from(input.files || []);
  const validFiles = selectedFiles.filter((file) => imageMimeTypes.includes(file.type));
  addFiles(toUploadedFiles(validFiles));
  input.value = "";
};

const triggerUpload = () => fileInputRef.value?.click();

const removeFile = (id: string) => {
  const idx = files.value.findIndex((f) => f.id === id);
  files.value = files.value.filter((uploaded) => uploaded.id !== id);
  const next = new Map(fileStatuses.value);
  next.delete(id);
  fileStatuses.value = next;

  const nextManual = new Map(manualBoxes.value);
  nextManual.delete(id);
  manualBoxes.value = nextManual;
  const nextPreview = new Map(previewRegions.value);
  nextPreview.delete(id);
  previewRegions.value = nextPreview;
  const nextOverrides = new Map(pageOverrides.value);
  nextOverrides.delete(id);
  pageOverrides.value = nextOverrides;

  if (currentId.value === id) {
    const fallback = files.value[idx] ?? files.value[idx - 1] ?? files.value[0];
    currentId.value = fallback ? fallback.id : null;
  }
};

const clearForm = () => {
  files.value = [];
  fileStatuses.value = new Map();
  currentId.value = null;
  manualBoxes.value = new Map();
  previewRegions.value = new Map();
  pageOverrides.value = new Map();
};

const addManualBox = (box: ManualBox) => {
  if (!currentId.value) return;
  const next = new Map(manualBoxes.value);
  next.set(currentId.value, [...(next.get(currentId.value) ?? []), box]);
  manualBoxes.value = next;
};

const removeManualBox = (index: number) => {
  if (!currentId.value) return;
  const next = new Map(manualBoxes.value);
  const list = [...(next.get(currentId.value) ?? [])];
  list.splice(index, 1);
  next.set(currentId.value, list);
  manualBoxes.value = next;
};

const buildSavedStory = async (name: string): Promise<SavedStory> => {
  const pages = await Promise.all(
    files.value.map(async (uploaded) => {
      const status = fileStatuses.value.get(uploaded.id);
      const imageDataUrl = await blobToDataUrl(uploaded.file);
      const resultDataUrl = status?.result ? await blobToDataUrl(status.result) : null;
      return { id: uploaded.id, originalName: uploaded.file.name, imageDataUrl, resultDataUrl };
    })
  );
  return {
    id: `story-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    name,
    createdAt: new Date().toISOString(),
    settings: currentSettings(),
    storyContext: { projectName: projectName.value, glossary: glossary.value },
    pages,
  };
};

const confirmSaveStory = async (name: string) => {
  const story = await buildSavedStory(name);
  saveStories([...loadStories(), story]);
  showSaveStoryDialog.value = false;
  clearForm();
};

const clearGallery = () => {
  finishedImages.value = [];
  localStorage.removeItem("manga-translator-finished-images");
};

const downloadCurrent = () => {
  if (!currentStatus.value?.result || !currentFile.value) return;
  const url = URL.createObjectURL(currentStatus.value.result);
  const a = document.createElement("a");
  a.href = url;
  a.download = currentFile.value.file.name.replace(/\.[^.]+$/, "") + "-translated.png";
  a.click();
  URL.revokeObjectURL(url);
};

// Status bookkeeping
const resetFileStatuses = () => {
  const next = new Map<string, FileStatus>();
  files.value.forEach((uploaded) => {
    next.set(uploaded.id, { status: null, progress: null, queuePos: null, result: null, error: null });
  });
  fileStatuses.value = next;
};

const updateFileStatus = (fileId: string, update: Partial<FileStatus>) => {
  const next = new Map(fileStatuses.value);
  const current = next.get(fileId) || { status: null, progress: null, queuePos: null, result: null, error: null };
  next.set(fileId, { ...current, ...update });
  fileStatuses.value = next;
};

const recordFinishedImage = (fileId: string, originalName: string, result: Blob) => {
  const finishedImage: FinishedImage = {
    id: `${fileId}-${Date.now()}`,
    originalName,
    result,
    finishedAt: new Date(),
    settings: resolvedSettingsFor(fileId),
  };
  finishedImages.value = [finishedImage, ...finishedImages.value];
  addFinishedImage(finishedImage);

  if (translator.value === "custom_openai") rightDockRef.value?.markEndpointVerified();
};

const processStatusUpdate = (statusCode: number, decodedData: string, fileId: string, data: Uint8Array) => {
  switch (statusCode) {
    case 0: {
      // result returned
      const resultBlob = new Blob([data], { type: "image/png" });
      updateFileStatus(fileId, { status: "finished", result: resultBlob });
      const originalName = files.value.find((uploaded) => uploaded.id === fileId)?.file.name ?? fileId;
      recordFinishedImage(fileId, originalName, resultBlob);
      break;
    }
    case 1: // translating / progress status
      updateFileStatus(fileId, { status: decodedData as StatusKey });
      break;
    case 2: // error
      updateFileStatus(fileId, { status: "error", error: decodedData });
      break;
    case 3: // queued
      updateFileStatus(fileId, { status: "pending", queuePos: decodedData });
      break;
    case 4: // queue cleared
      updateFileStatus(fileId, { status: "pending", queuePos: null });
      break;
    default:
      console.warn(`Unknown status code ${statusCode} for file ${fileId}`);
      break;
  }
};

// Streaming (single-file) translation
const requestTranslation = async (file: File, config: string) => {
  const formData = new FormData();
  formData.append("image", file);
  formData.append("config", config);

  const response = await fetch(`/api/translate/with-form/image/stream`, {
    method: "POST",
    body: formData,
  });

  if (response.status !== 200) {
    throw new Error("Upload failed");
  }

  return response;
};

const processChunk = (value: Uint8Array, fileId: string, currentBuffer: Uint8Array): Uint8Array => {
  if (fileStatuses.value.get(fileId)?.error) {
    throw new Error(`Processing stopped due to previous error for file ${fileId}`);
  }

  const newBuffer = new Uint8Array(currentBuffer.length + value.length);
  newBuffer.set(currentBuffer);
  newBuffer.set(value, currentBuffer.length);
  let processedBuffer = newBuffer;

  while (processedBuffer.length >= 5) {
    const dataSize = new DataView(processedBuffer.buffer).getUint32(1, false);
    const totalSize = 5 + dataSize;
    if (processedBuffer.length < totalSize) break;

    const statusCode = processedBuffer[0];
    const data = processedBuffer.slice(5, totalSize);
    const decodedData = new TextDecoder("utf-8").decode(data);

    processStatusUpdate(statusCode, decodedData, fileId, data);
    processedBuffer = processedBuffer.slice(totalSize);
  }

  return processedBuffer;
};

const processSingleFileStream = async (uploaded: UploadedFile, config: string) => {
  const { id, file } = uploaded;
  try {
    const response = await requestTranslation(file, config);
    const reader = response.body?.getReader();
    if (!reader) throw new Error("Failed to get stream reader");

    let fileBuffer = new Uint8Array();

    while (true) {
      const { done, value } = await reader.read();
      if (done || !value) break;

      try {
        fileBuffer = processChunk(value, id, fileBuffer);
      } catch (error) {
        console.error(`Error processing chunk for ${file.name}:`, error);
        updateFileStatus(id, {
          status: "error",
          error: error instanceof Error ? error.message : "Error processing chunk",
        });
      }
    }
  } catch (err) {
    console.error("Error processing file: ", file.name, err);
    updateFileStatus(id, { status: "error", error: err instanceof Error ? err.message : "Unknown error" });
  }
};

// Per-page config: each page can have its own resolved settings (see pageOverrides above)
// and its own manually-marked text boxes, so this is built per page rather than once.
const buildTranslationConfigObjectFor = (pageId: string) => {
  const s = resolvedSettingsFor(pageId);
  const manual = manualBoxes.value.get(pageId);
  return {
    detector: {
      detector: s.textDetector,
      detection_size: s.detectionResolution,
      box_threshold: s.customBoxThreshold,
      unclip_ratio: s.customUnclipRatio,
      ...(manual && manual.length ? { manual_text_boxes: manual } : {}),
    },
    render: {
      direction: s.renderTextDirection,
    },
    translator: {
      translator: s.translator,
      target_lang: s.targetLanguage,
      ...(s.translator === "custom_openai" && endpoint.value
        ? {
            custom_openai_base_url: endpoint.value.baseUrl,
            custom_openai_model: endpoint.value.model || null,
            custom_openai_api_key: endpoint.value.apiKey || null,
          }
        : {}),
    },
    inpainter: {
      inpainter: s.inpainter,
      inpainting_size: s.inpaintingSize,
    },
    colorizer: {
      colorizer: s.colorizer,
    },
    ocr: {
      ocr: s.ocr,
    },
    mask_dilation_offset: s.maskDilationOffset,
  };
};

const fileToDataUrl = blobToDataUrl;

const processBatchTranslation = async () => {
  const configs = files.value.map(({ id }) => buildTranslationConfigObjectFor(id));

  files.value.forEach(({ id }) => updateFileStatus(id, { status: "translating" }));

  try {
    const images = await Promise.all(files.value.map((uploaded) => fileToDataUrl(uploaded.file)));

    const response = await fetch(`/api/translate/batch/json-images`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ images, configs, batch_size: files.value.length }),
    });

    if (!response.ok) throw new Error(`Batch translation failed: ${response.status}`);

    const results: (string | null)[] = await response.json();

    files.value.forEach(({ id, file }, index) => {
      const dataUrl = results[index];
      if (!dataUrl) {
        updateFileStatus(id, { status: "error", error: "No result returned for this page" });
        return;
      }

      const resultBlob = dataUrlToBlob(dataUrl);
      updateFileStatus(id, { status: "finished", result: resultBlob });
      recordFinishedImage(id, file.name, resultBlob);
    });
  } catch (err) {
    console.error("Batch translation failed:", err);
    files.value.forEach(({ id }) =>
      updateFileStatus(id, {
        status: "error",
        error: err instanceof Error ? err.message : "Batch translation failed",
      })
    );
  }
};

const processTranslation = async () => {
  // Multiple pages: translate together in one batch so the translator gets full-story
  // context instead of only the current page.
  if (files.value.length > 1) {
    await processBatchTranslation();
    return;
  }

  try {
    await Promise.all(
      files.value.map((uploaded) =>
        processSingleFileStream(uploaded, JSON.stringify(buildTranslationConfigObjectFor(uploaded.id)))
      )
    );
  } catch (err) {
    console.error("Translation process failed:", err);
  }
};

const handleSubmit = () => {
  if (files.value.length === 0) return;
  resetFileStatuses();
  processTranslation();
};

const previewOcrError = ref<string | null>(null);

const previewOcr = async () => {
  if (!currentFile.value || !currentId.value) return;
  const pageId = currentId.value;
  isPreviewingOcr.value = true;
  previewOcrError.value = null;
  try {
    const formData = new FormData();
    formData.append("image", currentFile.value.file);
    formData.append("config", JSON.stringify(buildTranslationConfigObjectFor(pageId)));

    const response = await fetch("/api/translate/with-form/ocr-preview", { method: "POST", body: formData });
    if (!response.ok) throw new Error(`Preview failed: ${response.status}`);

    const data: { regions: OcrPreviewRegion[] } = await response.json();
    const next = new Map(previewRegions.value);
    next.set(pageId, data.regions);
    previewRegions.value = next;
  } catch (err) {
    console.error("OCR preview failed:", err);
    previewOcrError.value = err instanceof Error ? err.message : "OCR preview failed";
  } finally {
    isPreviewingOcr.value = false;
  }
};
</script>

<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <AppHeader
      :current-label="currentFile?.file.name ?? null"
      :page-index="currentIndex < 0 ? 0 : currentIndex"
      :page-count="files.length"
      :has-files="files.length > 0"
      :is-processing="isProcessing"
      :is-all-finished="isProcessingAllFinished"
      :current-is-finished="currentStatus?.status === 'finished'"
      :is-previewing-ocr="isPreviewingOcr"
      @upload-click="triggerUpload"
      @translate="handleSubmit"
      @preview-ocr="previewOcr"
      @download-current="downloadCurrent"
      @clear="clearForm"
      @save-as-story="showSaveStoryDialog = true"
    />

    <div class="flex flex-1 min-h-0">
      <ToolRail v-model:tool="tool" v-model:zoom="zoom" @upload-click="triggerUpload" />

      <CanvasViewport
        :file="currentFile?.file ?? null"
        :result="currentStatus?.result ?? null"
        :status="currentStatus"
        :zoom="zoom"
        :tool="tool"
        :manual-boxes="currentId ? manualBoxes.get(currentId) ?? [] : []"
        :preview-regions="currentId ? previewRegions.get(currentId) ?? null : null"
        :extra-error="previewOcrError"
        @drop="handleDrop"
        @file-change="handleFileChange"
        @add-manual-box="addManualBox"
        @remove-manual-box="removeManualBox"
      />

      <RightDock
        ref="rightDockRef"
        v-model:endpoint="endpoint"
        v-model:pageOverrideEnabled="pageOverrideEnabled"
        v-model:detectionResolution="detectionResolutionField"
        v-model:textDetector="textDetectorField"
        v-model:renderTextDirection="renderTextDirectionField"
        v-model:translator="translatorField"
        v-model:targetLanguage="targetLanguageField"
        v-model:inpaintingSize="inpaintingSizeField"
        v-model:customUnclipRatio="customUnclipRatioField"
        v-model:customBoxThreshold="customBoxThresholdField"
        v-model:maskDilationOffset="maskDilationOffsetField"
        v-model:inpainter="inpainterField"
        v-model:colorizer="colorizerField"
        v-model:ocr="ocrField"
        v-model:projectName="projectName"
        v-model:glossary="glossary"
        :finished-images="finishedImages"
        :current-page-label="currentFile?.file.name ?? null"
        @clear-gallery="clearGallery"
      />
    </div>

    <PageFilmstrip
      :files="files"
      :file-statuses="fileStatuses"
      :current-id="currentId"
      :is-processing="isProcessing"
      :is-processing-all-finished="isProcessingAllFinished"
      @select="(id) => (currentId = id)"
      @remove="removeFile"
      @upload-click="triggerUpload"
    />

    <input
      ref="fileInputRef"
      type="file"
      multiple
      accept="image/png,image/jpeg,image/bmp,image/webp"
      class="hidden"
      @change="handleFileChange"
    />

    <SaveStoryDialog
      :open="showSaveStoryDialog"
      :default-name="projectName"
      :page-count="files.length"
      @close="showSaveStoryDialog = false"
      @confirm="confirmSaveStory"
    />
  </div>
</template>
