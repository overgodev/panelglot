<script setup lang="ts">
import type { TranslatorKey, FinishedImage, CustomEndpoint } from "~/types";
import { validTranslators } from "~/types";
import {
  languageOptions,
  detectionResolutions,
  textDetectorOptions,
  ocrOptions,
  inpaintingSizes,
  inpainterOptions,
  colorizerOptions,
} from "~/config";

const detectionResolution = defineModel<string>("detectionResolution", { required: true });
const textDetector = defineModel<string>("textDetector", { required: true });
const renderTextDirection = defineModel<string>("renderTextDirection", { required: true });
const translator = defineModel<TranslatorKey>("translator", { required: true });
const targetLanguage = defineModel<string>("targetLanguage", { required: true });
const inpaintingSize = defineModel<string>("inpaintingSize", { required: true });
const customUnclipRatio = defineModel<number>("customUnclipRatio", { required: true });
const customBoxThreshold = defineModel<number>("customBoxThreshold", { required: true });
const maskDilationOffset = defineModel<number>("maskDilationOffset", { required: true });
const ocr = defineModel<string>("ocr", { required: true });
const inpainter = defineModel<string>("inpainter", { required: true });
const colorizer = defineModel<string>("colorizer", { required: true });
const projectName = defineModel<string>("projectName", { required: true });
const glossary = defineModel<string>("glossary", { required: true });
const endpoint = defineModel<CustomEndpoint | null>("endpoint", { required: true });
const pageOverrideEnabled = defineModel<boolean>("pageOverrideEnabled", { required: true });

defineProps<{
  finishedImages: FinishedImage[];
  currentPageLabel: string | null;
}>();

defineEmits<{ (e: "clear-gallery"): void }>();

const endpointPickerRef = ref<{ markVerified: () => void } | null>(null);
defineExpose({ markEndpointVerified: () => endpointPickerRef.value?.markVerified() });

const detectionResolutionOptions = detectionResolutions.map((res) => ({ label: `${res}px`, value: String(res) }));
const inpaintingSizeOptions = inpaintingSizes.map((size) => ({ label: `${size}px`, value: String(size) }));
const translatorOptions = validTranslators.map((key) => ({ value: key, label: getTranslatorName(key) }));
const renderDirectionOptions = [
  { value: "auto", label: "Auto" },
  { value: "horizontal", label: "Horizontal" },
  { value: "vertical", label: "Vertical" },
];
</script>

<template>
  <aside
    class="w-[300px] shrink-0 border-l overflow-y-auto"
    style="background: var(--color-surface); border-color: var(--color-border)"
  >
    <div v-if="currentPageLabel" class="page-scope-bar">
      <label class="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" v-model="pageOverrideEnabled" class="accent-current" style="color: var(--color-accent)" />
        <span class="text-xs" style="color: var(--color-text-secondary)">
          Custom settings for <strong style="color: var(--color-text)">{{ currentPageLabel }}</strong>
        </span>
      </label>
      <p class="text-[11px] mt-1" style="color: var(--color-text-tertiary)">
        {{
          pageOverrideEnabled
            ? "Editing settings below only affects this page."
            : "Off — this page uses the settings below, shared with every other page."
        }}
      </p>
    </div>

    <details open>
      <summary>Translation</summary>
      <div class="section-body">
        <LabeledSelect id="translator" label="Translator" v-model="translator" :options="translatorOptions" />
        <EndpointPicker v-if="translator === 'custom_openai'" ref="endpointPickerRef" v-model:selected="endpoint" />
        <LabeledSelect id="targetLanguage" label="Target Language" v-model="targetLanguage" :options="languageOptions" />
        <LabeledSelect
          id="renderTextDirection"
          label="Render Direction"
          v-model="renderTextDirection"
          :options="renderDirectionOptions"
        />
      </div>
    </details>

    <details>
      <summary>Detection</summary>
      <div class="section-body">
        <LabeledSelect
          id="detectionResolution"
          label="Detection Resolution"
          v-model="detectionResolution"
          :options="detectionResolutionOptions"
        />
        <LabeledSelect id="textDetector" label="Text Detector" v-model="textDetector" :options="textDetectorOptions" />
        <LabeledSelect
          id="ocr"
          label="OCR Model"
          title="Which language the OCR reads best"
          v-model="ocr"
          :options="ocrOptions"
        />
        <div class="grid grid-cols-2 gap-2">
          <LabeledInput
            id="boxThreshold"
            label="Box Threshold"
            title="Confidence threshold for keeping a detected text box. Lower catches more text but is noisier; higher misses faint or small text."
            :step="0.01"
            v-model="customBoxThreshold"
          />
          <LabeledInput
            id="unclipRatio"
            label="Unclip Ratio"
            title="How far to expand a detected text region outward from its skeleton into a full bounding box. Higher covers more of the bubble/text edges; too high starts overlapping neighboring text."
            :step="0.01"
            v-model="customUnclipRatio"
          />
        </div>
        <LabeledInput
          id="maskDilationOffset"
          label="Mask Dilation Offset"
          title="How far to expand the inpainting mask beyond the detected text, in pixels. Prevents leftover original-text pixels around the edges; too high erases nearby art."
          :step="1"
          v-model="maskDilationOffset"
        />
      </div>
    </details>

    <details>
      <summary>Inpainting</summary>
      <div class="section-body">
        <LabeledSelect id="inpainter" label="Inpainter" v-model="inpainter" :options="inpainterOptions" />
        <LabeledSelect id="inpaintingSize" label="Inpainting Size" v-model="inpaintingSize" :options="inpaintingSizeOptions" />
      </div>
    </details>

    <details>
      <summary>Colorization</summary>
      <div class="section-body">
        <LabeledSelect
          id="colorizer"
          label="Model"
          title="Colorize the page before translation is rendered"
          v-model="colorizer"
          :options="colorizerOptions"
        />
      </div>
    </details>

    <details>
      <summary>Story Context</summary>
      <div class="section-body">
        <div class="flex flex-col gap-1">
          <label for="projectName" class="text-xs font-medium" style="color: var(--color-text-secondary)">
            Project / Story Name
          </label>
          <input
            id="projectName"
            v-model="projectName"
            type="text"
            placeholder="e.g. Frieren: Beyond Journey's End"
            class="story-input"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label for="glossary" class="text-xs font-medium" style="color: var(--color-text-secondary)">
            Characters &amp; Glossary
          </label>
          <textarea
            id="glossary"
            v-model="glossary"
            rows="5"
            placeholder="Character names, honorifics, terminology, tone notes…"
            class="story-input resize-none"
          />
        </div>
        <p class="text-[11px] leading-snug" style="color: var(--color-text-tertiary)">
          Saved locally to this browser. Will be sent as translation context in a future update.
        </p>
      </div>
    </details>

    <details>
      <summary>
        History
        <span v-if="finishedImages.length" class="ml-auto font-mono text-[10px]" style="color: var(--color-text-tertiary)">
          {{ finishedImages.length }}
        </span>
      </summary>
      <div class="section-body">
        <ResultGallery :finished-images="finishedImages" @clear-gallery="$emit('clear-gallery')" />
      </div>
    </details>
  </aside>
</template>

<style scoped>
details {
  border-bottom: 1px solid var(--color-border);
}

summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 11px 14px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  cursor: pointer;
  list-style: none;
  user-select: none;
}

summary::-webkit-details-marker {
  display: none;
}

summary::before {
  content: "";
  width: 8px;
  height: 8px;
  border-right: 1.5px solid var(--color-text-tertiary);
  border-bottom: 1.5px solid var(--color-text-tertiary);
  transform: rotate(-45deg);
  transition: transform 140ms ease;
  flex-shrink: 0;
}

details[open] > summary::before {
  transform: rotate(45deg);
}

summary:hover {
  color: var(--color-text);
}

.section-body {
  padding: 4px 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.story-input {
  width: 100%;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-sunken);
  color: var(--color-text);
  padding: 7px 10px;
  font-size: 13px;
  transition: border-color 120ms ease;
}

.story-input:focus {
  border-color: var(--color-accent);
  outline: none;
}

.page-scope-bar {
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-accent-soft);
}
</style>
