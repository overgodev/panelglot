<script setup lang="ts">
import type { FileStatus, UploadedFile } from "~/types";

defineProps<{
  files: UploadedFile[];
  fileStatuses: Map<string, FileStatus>;
  currentId: string | null;
  isProcessing: boolean;
  isProcessingAllFinished: boolean;
}>();

const emit = defineEmits<{
  (e: "select", id: string): void;
  (e: "remove", id: string): void;
  (e: "upload-click"): void;
}>();

const thumbUrl = (file: File, result: Blob | null): string => URL.createObjectURL(result ?? file);
</script>

<template>
  <div
    class="flex items-center gap-2.5 h-24 px-3 border-t overflow-x-auto shrink-0"
    style="background: var(--color-surface); border-color: var(--color-border)"
  >
    <button
      v-for="{ id, file } in files"
      :key="id"
      type="button"
      class="thumb group"
      :class="{ active: id === currentId }"
      @click="emit('select', id)"
    >
      <img :src="thumbUrl(file, fileStatuses.get(id)?.result ?? null)" :alt="file.name" />

      <span v-if="fileStatuses.get(id)?.error" class="thumb-badge" style="background: var(--color-danger)">
        <Icon name="alert" :size="10" />
      </span>
      <span
        v-else-if="fileStatuses.get(id)?.status === 'finished'"
        class="thumb-badge"
        style="background: var(--color-success)"
      >
        <Icon name="check" :size="10" />
      </span>
      <span
        v-else-if="fileStatuses.get(id)"
        class="thumb-badge"
        style="background: var(--color-accent)"
      >
        <span class="w-2 h-2 rounded-full border animate-spin" style="border-color: #17110a; border-top-color: transparent" />
      </span>

      <button
        v-if="!isProcessing && !isProcessingAllFinished"
        type="button"
        class="thumb-remove"
        title="Remove page"
        @click.stop="emit('remove', id)"
      >
        <Icon name="close" :size="11" />
      </button>
    </button>

    <button
      v-if="!isProcessing"
      type="button"
      class="add-tile"
      title="Add pages"
      @click="emit('upload-click')"
    >
      <Icon name="plus" :size="18" />
    </button>
  </div>
</template>

<style scoped>
.thumb {
  position: relative;
  flex-shrink: 0;
  width: 60px;
  height: 78px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1.5px solid var(--color-border);
  transition: border-color 120ms ease;
}

.thumb:hover {
  border-color: var(--color-border-strong);
}

.thumb.active {
  border-color: var(--color-accent);
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-badge {
  position: absolute;
  bottom: 3px;
  right: 3px;
  width: 15px;
  height: 15px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #17110a;
}

.thumb-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 16px;
  height: 16px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 12, 0.75);
  color: #fff;
  opacity: 0;
  transition: opacity 120ms ease;
}

.thumb:hover .thumb-remove {
  opacity: 1;
}

.add-tile {
  flex-shrink: 0;
  width: 60px;
  height: 78px;
  border-radius: var(--radius-sm);
  border: 1.5px dashed var(--color-border-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  transition: border-color 120ms ease, color 120ms ease;
}

.add-tile:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
</style>
