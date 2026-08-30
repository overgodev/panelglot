<script setup lang="ts">
defineProps<{
  currentLabel: string | null;
  pageIndex: number;
  pageCount: number;
  hasFiles: boolean;
  isProcessing: boolean;
  isAllFinished: boolean;
  currentIsFinished: boolean;
  isPreviewingOcr: boolean;
}>();

const emit = defineEmits<{
  (e: "upload-click"): void;
  (e: "translate"): void;
  (e: "preview-ocr"): void;
  (e: "download-current"): void;
  (e: "clear"): void;
  (e: "save-as-story"): void;
}>();
</script>

<template>
  <header
    class="flex items-center gap-4 h-14 px-4 border-b shrink-0"
    style="background: var(--color-surface); border-color: var(--color-border)"
  >
    <div class="flex items-center gap-2.5 shrink-0">
      <Icon name="book" :size="19" style="color: var(--color-accent)" />
      <span class="font-semibold tracking-tight text-[15px]" style="font-family: var(--font-display); color: var(--color-text)">
        Panelglot
      </span>
    </div>

    <NuxtLink to="/stories" class="btn-ghost shrink-0">
      <Icon name="layers" :size="15" />
      <span>Stories</span>
    </NuxtLink>

    <div class="h-5 w-px shrink-0" style="background: var(--color-border)" />

    <div class="flex-1 min-w-0 flex items-center gap-2 text-sm" style="color: var(--color-text-secondary)">
      <template v-if="hasFiles">
        <span class="truncate" style="color: var(--color-text)">{{ currentLabel }}</span>
        <span class="font-mono text-xs shrink-0" style="color: var(--color-text-tertiary)">
          Page {{ pageIndex + 1 }} / {{ pageCount }}
        </span>
      </template>
      <span v-else>No pages loaded yet</span>
    </div>

    <div class="flex items-center gap-2 shrink-0">
      <button
        type="button"
        class="btn-ghost"
        @click="emit('upload-click')"
      >
        <Icon name="upload" :size="15" />
        <span>Upload</span>
      </button>

      <button
        v-if="currentIsFinished"
        type="button"
        class="btn-ghost"
        @click="emit('download-current')"
      >
        <Icon name="download" :size="15" />
        <span>Export</span>
      </button>

      <button
        v-if="hasFiles && !isProcessing"
        type="button"
        class="btn-ghost"
        @click="emit('save-as-story')"
      >
        <Icon name="book" :size="15" />
        <span>Save as Story</span>
      </button>

      <button
        v-if="hasFiles && !isProcessing"
        type="button"
        class="btn-ghost"
        @click="emit('clear')"
      >
        <Icon name="trash" :size="15" />
        <span>Clear</span>
      </button>

      <button
        v-if="hasFiles && !isProcessing && !isAllFinished"
        type="button"
        class="btn-ghost"
        :disabled="isPreviewingOcr"
        title="Run detection + OCR only and show what text was caught, without translating"
        @click="emit('preview-ocr')"
      >
        <span
          v-if="isPreviewingOcr"
          class="w-3 h-3 rounded-full border-2 animate-spin shrink-0"
          style="border-color: var(--color-text-secondary); border-top-color: transparent"
        />
        <Icon v-else name="image" :size="15" />
        <span>Preview OCR</span>
      </button>

      <button
        v-if="hasFiles && !isProcessing && !isAllFinished"
        type="button"
        class="btn-accent"
        @click="emit('translate')"
      >
        Translate All
      </button>
    </div>
  </header>
</template>

<style scoped>
.btn-ghost {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 11px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  transition: background-color 120ms ease, color 120ms ease, border-color 120ms ease;
}

.btn-ghost:hover:not(:disabled) {
  color: var(--color-text);
  border-color: var(--color-border-strong);
  background: var(--color-surface-raised);
}

.btn-ghost:disabled {
  opacity: 0.5;
}

.btn-accent {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius-md);
  color: #17110a;
  background: var(--color-accent);
  transition: background-color 120ms ease;
}

.btn-accent:hover {
  background: var(--color-accent-strong);
}
</style>
