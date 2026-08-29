<script setup lang="ts">
import type { FileStatus, UploadedFile } from "~/types";

defineProps<{
  files: UploadedFile[];
  fileStatuses: Map<string, FileStatus>;
  isProcessing: boolean;
  isProcessingAllFinished: boolean;
}>();

const emit = defineEmits<{
  (e: "file-change", event: Event): void;
  (e: "drop", event: DragEvent): void;
  (e: "submit"): void;
  (e: "clear"): void;
  (e: "remove", id: string): void;
}>();
</script>

<template>
  <div class="space-y-4 max-w-[1200px] mx-auto">
    <form v-if="!isProcessing && !isProcessingAllFinished">
      <label
        for="file"
        class="block p-4 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer"
        @drop.prevent="emit('drop', $event)"
        @dragover.prevent
        @dragenter.prevent
        @dragleave.prevent
      >
        <div class="text-center p-8">
          <div class="text-3xl mb-2">⬆️</div>
          <div class="mt-2 text-gray-600">
            Drop images here or click to select and upload images
          </div>
        </div>
        <input
          id="file"
          type="file"
          multiple
          accept="image/png,image/jpeg,image/bmp,image/webp"
          class="hidden"
          @change="emit('file-change', $event)"
        />
      </label>
    </form>

    <template v-if="files.length > 0">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mt-8">
        <div v-for="{ id, file } in files" :key="id" class="relative">
          <div class="relative w-full min-h-[400px] max-h-[600px] group">
            <button
              v-if="!isProcessing && !isProcessingAllFinished"
              type="button"
              @click="emit('remove', id)"
              class="absolute top-2 right-2 z-10 p-2 bg-red-500 rounded-lg text-white opacity-75 group-hover:opacity-100 transition-opacity hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              🗑️
            </button>

            <PreviewImage :file="file" :result="fileStatuses.get(id)?.result ?? null" />

            <div
              v-if="fileStatuses.get(id) && fileStatuses.get(id)!.status !== 'finished'"
              class="absolute inset-0 bg-black/50 flex items-center justify-center rounded-lg"
            >
              <div class="text-white text-center px-6 py-3 text-lg">
                {{
                  fetchStatusText(
                    fileStatuses.get(id)!.status,
                    fileStatuses.get(id)!.progress,
                    fileStatuses.get(id)!.queuePos,
                    fileStatuses.get(id)!.error
                  )
                }}
              </div>
            </div>
          </div>

          <div class="mt-3 flex justify-between items-center px-2">
            <div class="text-base truncate max-w-[80%] text-gray-700">{{ file.name }}</div>
            <div v-if="fileStatuses.get(id)?.error" class="text-red-500 text-base flex items-center">
              ⚠️ Error
            </div>
            <div v-else-if="fileStatuses.get(id)?.status === 'finished'" class="text-green-500 flex items-center">
              ✅
            </div>
          </div>
        </div>
      </div>

      <button
        v-if="!isProcessing && !isProcessingAllFinished"
        type="button"
        class="w-full mt-8 py-4 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg disabled:opacity-50"
        :disabled="files.length === 0"
        @click="emit('submit')"
      >
        Translate All Images
      </button>

      <button
        v-if="isProcessingAllFinished"
        type="button"
        class="w-full mt-8 py-4 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-lg"
        @click="emit('clear')"
      >
        Start Over
      </button>
    </template>
  </div>
</template>
