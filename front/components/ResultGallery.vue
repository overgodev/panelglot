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
  <div v-if="finishedImages.length === 0" class="text-center py-12 text-gray-500">
    <div class="text-4xl mb-4">🖼️</div>
    <p>No finished translations yet</p>
    <p class="text-sm">Completed translations will appear here</p>
  </div>

  <template v-else>
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-semibold text-gray-800">
        Translation Results ({{ finishedImages.length }})
      </h3>
      <button
        @click="emit('clear-gallery')"
        class="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md transition-colors"
      >
        Clear All
      </button>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      <div
        v-for="image in finishedImages"
        :key="image.id"
        class="group cursor-pointer bg-white rounded-lg border hover:border-blue-400 hover:shadow-md transition-all duration-200"
        @click="openImageModal(image)"
      >
        <div class="relative aspect-square overflow-hidden rounded-t-lg">
          <img
            :src="urlFor(image)"
            :alt="`Translated: ${image.originalName}`"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
          />
        </div>
        <div class="p-2">
          <div class="text-xs text-gray-600 truncate" :title="image.originalName">
            {{ image.originalName }}
          </div>
          <div class="text-xs text-gray-400">
            {{ new Date(image.finishedAt).toLocaleDateString() }}
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="isModalOpen && selectedImage"
      class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50"
      @click="closeImageModal"
    >
      <div class="relative max-w-[90vw] max-h-[90vh]" @click.stop>
        <button
          @click="navigateImage('prev')"
          class="absolute left-4 top-1/2 -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 transition-all z-10"
        >
          ‹
        </button>

        <button
          @click="navigateImage('next')"
          class="absolute right-4 top-1/2 -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 transition-all z-10"
        >
          ›
        </button>

        <button
          @click="closeImageModal"
          class="absolute top-4 right-4 bg-black bg-opacity-50 text-white p-2 rounded-full hover:bg-opacity-75 transition-all z-10"
        >
          ✕
        </button>

        <img
          :src="urlFor(selectedImage)"
          :alt="`Translated: ${selectedImage.originalName}`"
          class="max-w-full max-h-full object-contain"
        />

        <div class="absolute bottom-4 left-4 right-4 bg-black bg-opacity-50 text-white p-3 rounded-lg">
          <div class="text-sm font-medium">{{ selectedImage.originalName }}</div>
          <div class="text-xs text-gray-300">
            Completed: {{ new Date(selectedImage.finishedAt).toLocaleString() }}
          </div>
          <div class="text-xs text-gray-300">Translator: {{ selectedImage.settings.translator }}</div>
        </div>

        <div class="absolute bottom-20 left-1/2 -translate-x-1/2 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-xs">
          Use ← → arrow keys or click arrows to navigate
        </div>
      </div>
    </div>
  </template>
</template>
