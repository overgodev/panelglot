<script setup lang="ts">
import type { TranslatorKey } from "~/types";
import { validTranslators } from "~/types";
import {
  languageOptions,
  detectionResolutions,
  textDetectorOptions,
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
const inpainter = defineModel<string>("inpainter", { required: true });
const colorizer = defineModel<string>("colorizer", { required: true });

const detectionResolutionOptions = detectionResolutions.map((res) => ({
  label: `${res}px`,
  value: String(res),
}));

const inpaintingSizeOptions = inpaintingSizes.map((size) => ({
  label: `${size}px`,
  value: String(size),
}));

const translatorOptions = validTranslators.map((key) => ({
  value: key,
  label: getTranslatorName(key),
}));

const renderDirectionOptions = [
  { value: "auto", label: "Auto" },
  { value: "horizontal", label: "Horizontal" },
  { value: "vertical", label: "Vertical" },
];
</script>

<template>
  <div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      <LabeledSelect
        id="detectionResolution"
        label="Detection Resolution"
        title="Detection resolution"
        v-model="detectionResolution"
        :options="detectionResolutionOptions"
      />

      <LabeledSelect
        id="textDetector"
        label="Text Detector"
        title="Text detector"
        v-model="textDetector"
        :options="textDetectorOptions"
      />

      <LabeledSelect
        id="renderTextDirection"
        label="Render Direction"
        title="Render text orientation"
        v-model="renderTextDirection"
        :options="renderDirectionOptions"
      />

      <LabeledSelect
        id="translator"
        label="Translator"
        title="Translator"
        v-model="translator"
        :options="translatorOptions"
      />

      <LabeledSelect
        id="targetLanguage"
        label="Target Language"
        title="Target language"
        v-model="targetLanguage"
        :options="languageOptions"
      />
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mt-4">
      <LabeledSelect
        id="inpaintingSize"
        label="Inpainting Size"
        title="Inpainting size"
        v-model="inpaintingSize"
        :options="inpaintingSizeOptions"
      />

      <LabeledInput
        id="unclipRatio"
        label="Unclip Ratio"
        title="Unclip ratio"
        :step="0.01"
        v-model="customUnclipRatio"
      />

      <LabeledInput
        id="boxThreshold"
        label="Box Threshold"
        title="Box threshold"
        :step="0.01"
        v-model="customBoxThreshold"
      />

      <LabeledInput
        id="maskDilationOffset"
        label="Mask Dilation Offset"
        title="Mask dilation offset"
        :step="1"
        v-model="maskDilationOffset"
      />

      <LabeledSelect
        id="inpainter"
        label="Inpainter"
        title="Inpainter"
        v-model="inpainter"
        :options="inpainterOptions"
      />

      <LabeledSelect
        id="colorizer"
        label="Colorization"
        title="Colorize the page before translation is rendered"
        v-model="colorizer"
        :options="colorizerOptions"
      />
    </div>
  </div>
</template>
