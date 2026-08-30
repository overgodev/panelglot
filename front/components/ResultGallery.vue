<script setup lang="ts">
import type { FinishedImage } from "~/types";

const props = defineProps<{
  finishedImages: FinishedImage[];
}>();

const emit = defineEmits<{
  (e: "clear-gallery"): void;
}>();

const selectedImage = ref<FinishedImage | null>(null);
const isModalOpen = ref(false);

const objectUrls = new Map<string, string>();
const urlFor = (image: FinishedImage): string => {
  let url = objectUrls.get(image.id);
  if (!url) {
    url = URL.createObjectURL(image.result);
    objectUrls.set(image.id, url);
  }
  return url;
};

onBeforeUnmount(() => {
  objectUrls.forEach((url) => URL.revokeObjectURL(url));
});

const openImageModal = (image: FinishedImage) => {
  selectedImage.value = image;
  isModalOpen.value = true;
};

const closeImageModal = () => {
  isModalOpen.value = false;
  selectedImage.value = null;
};

const navigateImage = (direction: "prev" | "next") => {
  if (!selectedImage.value) return;

  const currentIndex = props.finishedImages.findIndex((img) => img.id === selectedImage.value!.id);
  if (currentIndex === -1) return;

  let newIndex: number;
  if (direction === "prev") {
    newIndex = currentIndex === 0 ? props.finishedImages.length - 1 : currentIndex - 1;
  } else {
    newIndex = currentIndex === props.finishedImages.length - 1 ? 0 : currentIndex + 1;
  }

  selectedImage.value = props.finishedImages[newIndex];
};

const handleKeyDown = (e: KeyboardEvent) => {
  if (!isModalOpen.value) return;

  switch (e.key) {
    case "Escape":
      closeImageModal();
      break;
    case "ArrowLeft":
      navigateImage("prev");
      break;
    case "ArrowRight":
      navigateImage("next");
      break;
  }
};

onMounted(() => window.addEventListener("keydown", handleKeyDown));
onBeforeUnmount(() => window.removeEventListener("keydown", handleKeyDown));
</script>

<template>
  <div v-if="finishedImages.length === 0" class="text-center py-6 text-sm" style="color: var(--color-text-tertiary)">
    <Icon name="image" :size="22" class="mx-auto mb-2" style="color: var(--color-text-tertiary)" />
    No finished translations yet
  </div>

  <template v-else>
    <div class="flex items-center justify-between">
      <span class="text-[11px]" style="color: var(--color-text-tertiary)">{{ finishedImages.length }} saved</span>
      <button
        @click="emit('clear-gallery')"
        class="text-[11px] font-medium transition-colors"
        style="color: var(--color-danger)"
      >
        Clear All
      </button>
    </div>

    <div class="grid grid-cols-3 gap-2 mt-2">
      <div
        v-for="image in finishedImages"
        :key="image.id"
        class="group cursor-pointer rounded-sm border overflow-hidden transition-colors"
        style="border-color: var(--color-border)"
        @click="openImageModal(image)"
      >
        <div class="relative aspect-square overflow-hidden">
          <img
            :src="urlFor(image)"
            :alt="`Translated: ${image.originalName}`"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          />
        </div>
      </div>
    </div>

    <div
      v-if="isModalOpen && selectedImage"
      class="fixed inset-0 flex items-center justify-center z-50"
      style="background: rgba(10, 10, 12, 0.85)"
      @click="closeImageModal"
    >
      <div class="relative max-w-[90vw] max-h-[90vh]" @click.stop>
        <button
          @click="navigateImage('prev')"
          class="modal-btn absolute left-4 top-1/2 -translate-y-1/2"
        >
          <Icon name="chevron-down" :size="16" class="rotate-90" />
        </button>

        <button
          @click="navigateImage('next')"
          class="modal-btn absolute right-4 top-1/2 -translate-y-1/2"
        >
          <Icon name="chevron-down" :size="16" class="-rotate-90" />
        </button>

        <button @click="closeImageModal" class="modal-btn absolute top-4 right-4">
          <Icon name="close" :size="16" />
        </button>

        <img
          :src="urlFor(selectedImage)"
          :alt="`Translated: ${selectedImage.originalName}`"
          class="max-w-full max-h-full object-contain rounded-sm"
        />

        <div class="absolute bottom-4 left-4 right-4 p-3 rounded-md" style="background: rgba(10, 10, 12, 0.75); color: var(--color-text)">
          <div class="text-sm font-medium">{{ selectedImage.originalName }}</div>
          <div class="text-xs" style="color: var(--color-text-tertiary)">
            Completed: {{ new Date(selectedImage.finishedAt).toLocaleString() }}
          </div>
          <div class="text-xs" style="color: var(--color-text-tertiary)">
            Translator: {{ selectedImage.settings.translator }}
          </div>
        </div>
      </div>
    </div>
  </template>
</template>

<style scoped>
.modal-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: rgba(10, 10, 12, 0.6);
  color: var(--color-text);
  z-index: 10;
  transition: background-color 120ms ease;
}

.modal-btn:hover {
  background: rgba(10, 10, 12, 0.85);
}
</style>
