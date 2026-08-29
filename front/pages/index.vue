<script setup lang="ts">
import {
  processingStatuses,
  type StatusKey,
  type TranslatorKey,
  type FileStatus,
  type TranslationSettings,
  type FinishedImage,
  type UploadedFile,
} from "~/types";
import { imageMimeTypes } from "~/config";

// State
const files = ref<UploadedFile[]>([]);
const fileStatuses = ref<Map<string, FileStatus>>(new Map());
const finishedImages = ref<FinishedImage[]>([]);

// Translation options
const detectionResolution = ref("1536");
const textDetector = ref("default");
const renderTextDirection = ref("auto");
const translator = ref<TranslatorKey>("youdao");
const targetLanguage = ref("CHS");

const inpaintingSize = ref("2048");
const customUnclipRatio = ref(2.3);
const customBoxThreshold = ref(0.7);
const maskDilationOffset = ref(30);
const inpainter = ref("default");
const colorizer = ref("none");

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
});

// Load saved settings / gallery, wire up paste handling
onMounted(() => {
  const saved = loadSettings();
  if (saved.detectionResolution) detectionResolution.value = saved.detectionResolution;
  if (saved.textDetector) textDetector.value = saved.textDetector;
  if (saved.renderTextDirection) renderTextDirection.value = saved.renderTextDirection;
  if (saved.translator) translator.value = saved.translator;
  if (saved.targetLanguage) targetLanguage.value = saved.targetLanguage;
  if (saved.inpaintingSize) inpaintingSize.value = saved.inpaintingSize;
  if (saved.customUnclipRatio) customUnclipRatio.value = saved.customUnclipRatio;
  if (saved.customBoxThreshold) customBoxThreshold.value = saved.customBoxThreshold;
  if (saved.maskDilationOffset) maskDilationOffset.value = saved.maskDilationOffset;
  if (saved.inpainter) inpainter.value = saved.inpainter;
  if (saved.colorizer) colorizer.value = saved.colorizer;

  finishedImages.value = loadFinishedImages();

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
  ],
  () => saveSettings(currentSettings())
);

// File handling
const toUploadedFiles = (rawFiles: File[]): UploadedFile[] =>
  rawFiles.map((file) => ({
    id: `${file.name}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    file,
  }));

const handlePaste = (e: ClipboardEvent) => {
  const items = e.clipboardData?.items || [];
  for (const item of items) {
    if (item.kind === "file") {
      const pastedFile = item.getAsFile();
      if (pastedFile && imageMimeTypes.includes(pastedFile.type)) {
        files.value = [...files.value, ...toUploadedFiles([pastedFile])];
        break;
      }
    }
  }
};

const handleDrop = (e: DragEvent) => {
  const droppedFiles = Array.from(e.dataTransfer?.files || []);
  const validFiles = droppedFiles.filter((file) => imageMimeTypes.includes(file.type));
  files.value = [...files.value, ...toUploadedFiles(validFiles)];
};

const handleFileChange = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const selectedFiles = Array.from(input.files || []);
  const validFiles = selectedFiles.filter((file) => imageMimeTypes.includes(file.type));
  files.value = [...files.value, ...toUploadedFiles(validFiles)];
  input.value = "";
};

const removeFile = (id: string) => {
  files.value = files.value.filter((uploaded) => uploaded.id !== id);
  const next = new Map(fileStatuses.value);
  next.delete(id);
  fileStatuses.value = next;
};

const clearForm = () => {
  files.value = [];
  fileStatuses.value = new Map();
};

const clearGallery = () => {
  finishedImages.value = [];
  localStorage.removeItem("manga-translator-finished-images");
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
    settings: currentSettings(),
  };
  finishedImages.value = [finishedImage, ...finishedImages.value];
  addFinishedImage(finishedImage);
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

// Whole-story batch translation
const buildTranslationConfigObject = () => ({
  detector: {
    detector: textDetector.value,
    detection_size: detectionResolution.value,
    box_threshold: customBoxThreshold.value,
    unclip_ratio: customUnclipRatio.value,
  },
  render: {
    direction: renderTextDirection.value,
  },
  translator: {
    translator: translator.value,
    target_lang: targetLanguage.value,
  },
  inpainter: {
    inpainter: inpainter.value,
    inpainting_size: inpaintingSize.value,
  },
  colorizer: {
    colorizer: colorizer.value,
  },
  mask_dilation_offset: maskDilationOffset.value,
});

const fileToDataUrl = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });

const dataUrlToBlob = (dataUrl: string): Blob => {
  const [, base64] = dataUrl.split(",", 2);
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: "image/png" });
};

const processBatchTranslation = async () => {
  const config = buildTranslationConfigObject();

  files.value.forEach(({ id }) => updateFileStatus(id, { status: "translating" }));

  try {
    const images = await Promise.all(files.value.map((uploaded) => fileToDataUrl(uploaded.file)));

    const response = await fetch(`/api/translate/batch/json-images`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ images, config, batch_size: files.value.length }),
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

  const config = JSON.stringify(buildTranslationConfigObject());
  try {
    await Promise.all(files.value.map((uploaded) => processSingleFileStream(uploaded, config)));
  } catch (err) {
    console.error("Translation process failed:", err);
  }
};

const handleSubmit = () => {
  if (files.value.length === 0) return;
  resetFileStatuses();
  processTranslation();
};
</script>

<template>
  <div>
    <AppHeader />
    <div class="bg-gray-100 min-h-screen flex flex-col pt-10 items-center">
      <div class="bg-white shadow-md rounded-lg p-6 w-full max-w-6xl space-y-6">
        <OptionsPanel
          v-model:detectionResolution="detectionResolution"
          v-model:textDetector="textDetector"
          v-model:renderTextDirection="renderTextDirection"
          v-model:translator="translator"
          v-model:targetLanguage="targetLanguage"
          v-model:inpaintingSize="inpaintingSize"
          v-model:customUnclipRatio="customUnclipRatio"
          v-model:customBoxThreshold="customBoxThreshold"
          v-model:maskDilationOffset="maskDilationOffset"
          v-model:inpainter="inpainter"
          v-model:colorizer="colorizer"
        />

        <div class="border-t pt-6">
          <ImageHandlingArea
            :files="files"
            :file-statuses="fileStatuses"
            :is-processing="isProcessing"
            :is-processing-all-finished="isProcessingAllFinished"
            @file-change="handleFileChange"
            @drop="handleDrop"
            @submit="handleSubmit"
            @clear="clearForm"
            @remove="removeFile"
          />
        </div>

        <div class="border-t pt-6">
          <ResultGallery :finished-images="finishedImages" @clear-gallery="clearGallery" />
        </div>
      </div>
    </div>
  </div>
</template>
